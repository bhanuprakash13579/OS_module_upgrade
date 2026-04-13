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

    def _suicide_if_parent_dies():
        import threading
        ppid = os.getppid()
        def _watch():
            import subprocess
            # CREATE_NO_WINDOW must be used without shell=True.
            # shell=True spawns an intermediate cmd.exe which Windows Terminal
            # briefly attaches to before CREATE_NO_WINDOW suppresses it —
            # causing a visible CMD flash every 5 seconds on Windows 11.
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            while True:
                try:
                    output = subprocess.check_output(
                        ['tasklist', '/FI', f'PID eq {ppid}', '/NH'],
                        creationflags=flags,
                        stdin=subprocess.DEVNULL,
                    ).decode('utf-8', errors='ignore')
                    if str(ppid) not in output:
                        raise Exception("Parent dead")
                except Exception:
                    os.kill(os.getpid(), signal.SIGTERM)
                    break
                time.sleep(5)
        threading.Thread(target=_watch, daemon=True).start()

    if sys.platform == "win32":
        _suicide_if_parent_dies()

    # ── SIGPIPE immunity ─────────────────────────────────────────────────────
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_IGN)

    cops_db = os.environ.get("COPS_DB_PATH", "")
    if cops_db:
        os.environ["COPS_DB_PATH"] = cops_db

    _slog(f"DB path: {cops_db or '(default)'}")

    def _free_port(port: int) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            try:
                s.connect(("127.0.0.1", port))
            except OSError:
                return

        try:
            import subprocess
            if sys.platform == "win32":
                _no_win = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
                result = subprocess.run(
                    ["netstat", "-ano"], capture_output=True, text=True,
                    creationflags=_no_win, stdin=subprocess.DEVNULL,
                )
                for line in result.stdout.splitlines():
                    if f":{port}" in line and "LISTENING" in line:
                        pid = line.strip().split()[-1]
                        subprocess.run(
                            ["taskkill", "/PID", pid, "/F"], capture_output=True,
                            creationflags=_no_win, stdin=subprocess.DEVNULL,
                        )
                        break
            else:
                cmd = ["fuser", f"{port}/tcp"] if sys.platform == "linux" else ["lsof", "-ti", f"tcp:{port}"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                for pid in result.stdout.split():
                    try: os.kill(int(pid.strip()), signal.SIGTERM)
                    except: pass
            time.sleep(0.8)
        except Exception as e:
            _slog(f"Note: could not free port {port}: {e}")

    _slog("checking port 8000...")
    _free_port(8000)
    _slog("port 8000 free")

    # Always redirect stdout/stderr to the log file with UTF-8 encoding.
    # On Windows, sys.stdout may be set to a cp1252 console handle even in
    # windowed (console=False) PyInstaller builds — printing any emoji or
    # non-Latin character raises UnicodeEncodeError and crashes the lifespan.
    try:
        sys.stdout = open(_LOG_PATH, "a", encoding="utf-8", buffering=1)
        sys.stderr = sys.stdout
    except Exception as _e:
        _slog(f"Warning: could not redirect stdout/stderr: {_e}")

    # Redirect stdin to a never-closing pipe so uvicorn
    # cannot exit due to EOF polling, while keeping fileno() functional.
    import io
    try:
        _r_fd, _w_fd = os.pipe()
        # Keep the write end open forever (never GC'd, never closed)
        _stdin_write_keeper = os.fdopen(_w_fd, "wb", buffering=0)
        sys.stdin = io.FileIO(_r_fd, "rb", closefd=True)
    except Exception as _pipe_err:
        _slog(f"Warning: could not create stdin pipe: {_pipe_err}")

    import logging
    # Pre-startup logging (sqlalchemy, asyncio, app imports)
    _file_handler = logging.FileHandler(_LOG_PATH, encoding="utf-8")
    _file_handler.setFormatter(logging.Formatter("[%(asctime)s] %(name)s %(levelname)s: %(message)s"))
    logging.root.addHandler(_file_handler)
    logging.root.setLevel(logging.DEBUG)

    _slog("importing uvicorn...")
    import uvicorn
    _slog("importing app.main...")
    from app.main import app
    _slog("app imported — starting uvicorn on 127.0.0.1:8000")

    # Pass log_config directly into uvicorn so its configure_logging() writes
    # to our file — uvicorn resets its own loggers on startup and would wipe
    # any handler we add before uvicorn.run().
    _uvicorn_log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {"format": "[%(asctime)s] %(name)s %(levelname)s: %(message)s"},
        },
        "handlers": {
            "file": {
                "class": "logging.FileHandler",
                "filename": str(_LOG_PATH),
                "formatter": "default",
                "encoding": "utf-8",
                "mode": "a",
            },
        },
        "loggers": {
            "uvicorn":        {"handlers": ["file"], "level": "DEBUG", "propagate": False},
            "uvicorn.error":  {"handlers": ["file"], "level": "DEBUG", "propagate": False},
            "uvicorn.access": {"handlers": ["file"], "level": "DEBUG", "propagate": False},
            "fastapi":        {"handlers": ["file"], "level": "DEBUG", "propagate": False},
            "sqlalchemy":     {"handlers": ["file"], "level": "INFO",  "propagate": False},
        },
    }

    if __name__ == "__main__":
        _slog("Entering uvicorn.run()...")
        _exit_ok = False
        try:
            uvicorn.run(
                app,
                host="127.0.0.1",
                port=8000,
                log_level="debug",
                access_log=False,
                log_config=_uvicorn_log_config,
            )
            _exit_ok = True
        finally:
            if _exit_ok:
                _slog("uvicorn.run() finished and returned gracefully!")
            else:
                _slog("uvicorn.run() exited unexpectedly (see errors above)")

except BaseException as e:
    _slog(f"FATAL STARTUP ERROR ({type(e).__name__} - {e}):\n" + traceback.format_exc())
    raise
