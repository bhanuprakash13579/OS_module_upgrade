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
src = open(path).read()
src = re.sub(r"_ADMIN_PWD_HASH = [^\n]+", "_ADMIN_PWD_HASH = " + repr(h), src)
open(path, "w").write(src)
print("Patched admin_auth.py: hash baked in.")
