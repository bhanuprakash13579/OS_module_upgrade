import sys
import sqlcipher3
import hashlib
from app.security.device import _BINDING_SECRET

db_path = "cops_br_database.db"
salt = b"cops-db-cipher-v1-2024-chennai-customs"
key_bytes = hashlib.pbkdf2_hmac("sha256", _BINDING_SECRET, salt, 100_000).hex()
pragma_key = f"x'{key_bytes}'"

print(f"Testing with key derived from: {_BINDING_SECRET}")

# Test normal SQLite page sizes
for pg_size in [1024, 2048, 4096, 8192, 16384, 32768, 65536]:
    for cipher_compat in [None, 3, 4]:
        try:
            conn = sqlcipher3.connect(db_path)
            conn.execute(f"PRAGMA key = \"{pragma_key}\"")
            if cipher_compat:
                conn.execute(f"PRAGMA cipher_compatibility = {cipher_compat}")
            conn.execute(f"PRAGMA cipher_page_size = {pg_size}")
            
            # Test if it's readable
            res = conn.execute("SELECT count(*) FROM sqlite_master").fetchone()
            print(f"SUCCESS! Database decrypted successfully with Page Size: {pg_size}, Compat: {cipher_compat}")
            sys.exit(0)
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except:
                pass

print("All combinations failed to decrypt the database.")
