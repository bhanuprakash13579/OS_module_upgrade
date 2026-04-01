import sys
import sqlcipher3
import hashlib

db_path = "cops_br_database.db"
salt = b"cops-db-cipher-v1-2024-chennai-customs"

# variations to try
passwords = [
    b"Cops@2026#",
    b"cops@2026#",
    b"COPS@2026#",
    b"cops@2024#",
    b"Cops@2024#",
    b"admin",
    b"password"
]

keys_to_try = []
for p in passwords:
    # 1. PBKDF2 derived hex key (like device.py)
    keys_to_try.append(f"x'{hashlib.pbkdf2_hmac('sha256', p, salt, 100_000).hex()}'")
    # 2. Raw string key
    keys_to_try.append(f"'{p.decode('utf-8')}'")

def try_key(pragma_key):
    for compat in [None, 3, 4]:
        try:
            conn = sqlcipher3.connect(db_path)
            conn.execute(f"PRAGMA key = \"{pragma_key}\"")
            if compat:
                conn.execute(f"PRAGMA cipher_compatibility = {compat}")
            conn.execute("SELECT count(*) FROM sqlite_master").fetchone()
            print(f"SUCCESS! Key: {pragma_key}, Compat: {compat}")
            return True
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except:
                pass
    return False

found = False
for k in keys_to_try:
    if try_key(k):
        found = True
        break

if not found:
    print("No valid key found among the common variations.")
