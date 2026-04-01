import sys
import sqlcipher3

db_path = "cops_br_database.db"
key = b"cops-db-cipher-v1-2024-chennai-customs"
import hashlib
from app.security.device import _BINDING_SECRET
key_bytes = hashlib.pbkdf2_hmac("sha256", _BINDING_SECRET, key, 100_000).hex()

print(f"Key: {key_bytes}")

for compat in [None, 3, 4]:
    try:
        conn = sqlcipher3.connect(db_path)
        conn.execute(f"PRAGMA key = \"x'{key_bytes}'\"")
        if compat:
            conn.execute(f"PRAGMA cipher_compatibility = {compat}")
        res = conn.execute("SELECT count(*) FROM sqlite_master").fetchone()
        print(f"Compat {compat} SUCCESS: {res}")
        sys.exit(0)
    except Exception as e:
        print(f"Compat {compat} failed: {e}")

