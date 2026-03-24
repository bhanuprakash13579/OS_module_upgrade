"""
Entry point for the PyInstaller-bundled COPS backend server.
Reads the DB path from the COPS_DB_PATH env variable (set by the Tauri sidecar)
and starts uvicorn on 0.0.0.0:8000.
"""
import os
import sys
import signal
import socket
import time
import datetime
import pathlib
import traceback

# ── Startup progress log ─────────────────────────────────────────────────────
# Written to TEMP so CI smoke tests and crash reports can read it.
# Works for both console=True and console=False (windowed) EXEs.
_LOG_PATH = pathlib.Path(
    os.environ.get("RUNNER_TEMP") or os.environ.get("TEMP") or "."
) / "cops_startup.log"

def _slog(msg: str) -> None:
    ts = datetime.datetime.now().isoformat(timespec="milliseconds")
    line = f"[{ts}] {msg}\n"
    try:
        with open(_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass
    # Also try stdout (works in console builds / dev mode)
    try:
        print(line, end="", flush=True)
    except Exception:
        pass


try:
    _slog("server_entry.py started")

    # ── SIGPIPE immunity ─────────────────────────────────────────────────────
    # When Tauri's async stdout/stderr reader closes (e.g. runtime hiccup),
    # the next write from Python or uvicorn would get SIGPIPE and kill the process.
    # Ignoring SIGPIPE converts it to a BrokenPipeError that uvicorn handles gracefully.
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_IGN)

    # ── Resolve DB path from env (set by Tauri lib.rs) ──────────────────────
    cops_db = os.environ.get("COPS_DB_PATH", "")
    if cops_db:
        os.environ["COPS_DB_PATH"] = cops_db

    _slog(f"DB path: {cops_db or '(default)'}")


    def _free_port(port: int) -> None:
        """Kill any orphaned process holding the given port (cross-platform)."""
        # Quick check: is port actually in use?
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            try:
                s.connect(("127.0.0.1", port))
            except OSError:
                return  # Port is free — nothing to do

        # Port is in use — find and kill the holder
        try:
            import subprocess
            if sys.platform == "win32":
                result = subprocess.run(
                    ["netstat", "-ano"], capture_output=True, text=True
                )
                for line in result.stdout.splitlines():
                    if f":{port}" in line and "LISTENING" in line:
                        pid = line.strip().split()[-1]
                        subprocess.run(
                            ["taskkill", "/PID", pid, "/F"], capture_output=True
                        )
                        break
            else:
                # Linux / macOS
                cmd = (
                    ["fuser", f"{port}/tcp"]
                    if sys.platform == "linux"
                    else ["lsof", "-ti", f"tcp:{port}"]
                )
                result = subprocess.run(cmd, capture_output=True, text=True)
                for pid in result.stdout.split():
                    try:
                        os.kill(int(pid.strip()), signal.SIGTERM)
                    except (ValueError, ProcessLookupError):
                        pass
            time.sleep(0.8)  # Give the process time to exit
        except Exception as e:
            _slog(f"Note: could not free port {port}: {e}")


    # Free port 8000 if a stale server is still running from a previous session
    _slog("checking port 8000...")
    _free_port(8000)
    _slog("port 8000 free")

    # ── Start the FastAPI app via uvicorn ────────────────────────────────────
    _slog("importing uvicorn...")
    import uvicorn
    _slog("importing app.main...")
    from app.main import app  # explicit import so PyInstaller bundles all deps
    _slog("app imported — starting uvicorn on 0.0.0.0:8000")

    # console=False (windowed EXE) sets sys.stdout = sys.stderr = None.
    # Uvicorn's DefaultFormatter calls sys.stdout.isatty() during logging
    # setup, which crashes with AttributeError on None. Redirect to the
    # startup log file so uvicorn output is also captured.
    if sys.stdout is None:
        sys.stdout = open(_LOG_PATH, "a", encoding="utf-8", buffering=1)
    if sys.stderr is None:
        sys.stderr = sys.stdout

    if sys.stdin is None:
        sys.stdin = open(os.devnull, "r")

    if __name__ == "__main__":
        # Bind to all interfaces so LAN clients (other PCs on the same network)
        # can access the app via browser. The LAN-only middleware in main.py still
        # blocks any non-private IP, so this is safe on an internal network.
        #
        # access_log=False: suppresses per-request stdout writes so a transient
        # broken pipe (SIGPIPE) from Tauri's stdout reader never kills the server.
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="warning",
            access_log=False,
        )

except BaseException as e:
    _slog(f"FATAL STARTUP ERROR ({type(e).__name__} - {e}):\n" + traceback.format_exc())
    raise
