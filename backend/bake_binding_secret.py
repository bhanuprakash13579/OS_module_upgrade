"""
CI helper — bakes BINDING_SECRET into device.py at build time.
Run via: python bake_binding_secret.py  (called from GitHub Actions before PyInstaller)
"""
import os
import re

secret = os.environ.get("BINDING_SECRET", "").strip()
if not secret:
    raise SystemExit("ERROR: BINDING_SECRET env var is not set.")
print(f"[bake_binding_secret] Secret length: {len(secret)} chars")

path = "app/security/device.py"
try:
    with open(path) as f:
        src = f.read()
except FileNotFoundError:
    raise SystemExit(f"ERROR: {path} not found. Working directory: {os.getcwd()}")

new_src = re.sub(
    r"_BINDING_SECRET: bytes = b\"[^\"]*\"",
    "_BINDING_SECRET: bytes = " + repr(secret.encode("utf-8")),
    src,
)
if new_src == src:
    raise SystemExit("ERROR: _BINDING_SECRET pattern not found in device.py — regex did not match.")

with open(path, "w") as f:
    f.write(new_src)
print("Patched device.py: BINDING_SECRET baked in.")
