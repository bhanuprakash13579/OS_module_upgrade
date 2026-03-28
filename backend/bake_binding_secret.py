"""
CI helper — XOR-encodes BINDING_SECRET and bakes it into device.py at build time.
Run via: python bake_binding_secret.py  (called from GitHub Actions before PyInstaller)

The password never appears as a plain string in the binary — only the XOR-encoded
bytes are stored, decoded at runtime using the key embedded in device.py.
"""
import os
import re

secret = os.environ.get("BINDING_SECRET", "").strip()
if not secret:
    raise SystemExit("ERROR: BINDING_SECRET env var is not set.")

print(f"[bake_binding_secret] Secret length: {len(secret)} chars")

# Must match _XK in device.py exactly
_XK = b"\xde\xad\xbe\xef\xca\xfe\xba\xbe\xde\xad\xbe\xef\xca\xfe"
secret_bytes = secret.encode("utf-8")
encoded_hex = bytes(b ^ _XK[i % len(_XK)] for i, b in enumerate(secret_bytes)).hex()

path = "app/security/device.py"
with open(path) as f:
    src = f.read()

new_src = re.sub(
    r'_ES = bytes\.fromhex\("[0-9a-f]*"\)',
    f'_ES = bytes.fromhex("{encoded_hex}")',
    src,
)
if new_src == src:
    raise SystemExit("ERROR: BAKE_TARGET pattern not found in device.py — regex did not match.")

with open(path, "w") as f:
    f.write(new_src)

print(f"[bake_binding_secret] Baked XOR-encoded secret into {path} ({len(secret_bytes)} bytes → {len(encoded_hex)//2} encoded bytes)")
