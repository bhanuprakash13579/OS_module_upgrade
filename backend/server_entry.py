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

# ── SIGPIPE immunity ─────────────────────────────────────────────────────────
# When Tauri's async stdout/stderr reader closes (e.g. runtime hiccup),
# the next write from Python or uvicorn would get SIGPIPE and kill the process.
# Ignoring SIGPIPE converts it to a BrokenPipeError that uvicorn handles gracefully.
if hasattr(signal, "SIGPIPE"):
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)

# ── Resolve DB path from env (set by Tauri lib.rs) ──────────────────────────
cops_db = os.environ.get("COPS_DB_PATH", "")
if cops_db:
    os.environ["COPS_DB_PATH"] = cops_db


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
        print(f"[cops] Note: could not free port {port}: {e}", flush=True)


# Free port 8000 if a stale server is still running from a previous session
_free_port(8000)

# ── Start the FastAPI app via uvicorn ────────────────────────────────────────
import uvicorn
from app.main import app  # explicit import so PyInstaller bundles all deps

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
