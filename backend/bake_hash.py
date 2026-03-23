"""
CI helper — bakes bcrypt hash of ADMIN_PASSWORD into admin_auth.py at build time.
Run via: python bake_hash.py  (called from GitHub Actions before PyInstaller)
"""
import os
import re
import bcrypt as _b

password = os.environ.get("ADMIN_PASSWORD", "")
if not password:
    raise SystemExit("ERROR: ADMIN_PASSWORD env var is not set.")

pw = password.encode("utf-8")
h = _b.hashpw(pw, _b.gensalt(12)).decode("utf-8")

path = "app/security/admin_auth.py"
try:
    with open(path) as f:
        src = f.read()
except FileNotFoundError:
    raise SystemExit(f"ERROR: {path} not found. Working directory: {os.getcwd()}")

new_src = re.sub(r"_ADMIN_PWD_HASH = [^\n]+", "_ADMIN_PWD_HASH = " + repr(h), src)
if new_src == src:
    raise SystemExit("ERROR: _ADMIN_PWD_HASH pattern not found in admin_auth.py — regex did not match.")

with open(path, "w") as f:
    f.write(new_src)
print("Patched admin_auth.py: hash baked in.")
