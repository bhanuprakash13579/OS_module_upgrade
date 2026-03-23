import bcrypt as _bcrypt


class _BcryptContext:
    """Drop-in replacement for passlib CryptContext(schemes=['bcrypt'])."""

    def verify(self, plain: str, hashed: str) -> bool:
        try:
            return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
        except Exception:
            return False

    def hash(self, password: str) -> str:
        return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt(12)).decode("utf-8")


pwd_context = _BcryptContext()
