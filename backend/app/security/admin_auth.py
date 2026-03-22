"""
System-admin credentials — hardcoded in the binary.

Security model
──────────────
• The admin password is stored ONLY as a bcrypt hash — never as plaintext.
• bcrypt is a one-way function: even if an attacker extracts this file from
  the compiled binary, they cannot reverse the hash to get the password.
• They would have to brute-force it (try millions of guesses), which is
  infeasible against bcrypt with a strong password.

To change the admin password before a release build:
  1. Run:  python3 -c "from passlib.context import CryptContext; \
                        c=CryptContext(schemes=['bcrypt'],deprecated='auto'); \
                        print(c.hash('YourNewPassword'))"
  2. Replace _ADMIN_PWD_HASH below with the printed output.
  3. Rebuild the binary (pyinstaller python-server.spec --noconfirm).
"""
import os
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Admin credentials (read from env or fallback to hardcoded hash) ─────────
# In production builds via GitHub Actions, ADMIN_PWD_HASH is injected as an env var.
_ADMIN_USERNAME = "sysadmin"
# ADMIN_PWD_HASH must be injected via environment variable at build time.
# If not set, the fallback is a deliberately invalid string so admin login
# is impossible in any build that was not produced by the secure CI pipeline.
_ADMIN_PWD_HASH = os.environ.get("ADMIN_PWD_HASH", "__ADMIN_PWD_HASH_NOT_CONFIGURED__")

_BEARER = HTTPBearer(auto_error=False)


def verify_admin_credentials(username: str, password: str) -> bool:
    """Return True only if username + password match the hardcoded admin."""
    if username != _ADMIN_USERNAME:
        return False
    try:
        return _ctx.verify(password, _ADMIN_PWD_HASH)
    except Exception:
        return False


def create_admin_token() -> str:
    """Issue a short-lived JWT for the system admin."""
    expire = datetime.utcnow() + timedelta(hours=8)
    return jwt.encode(
        {"sub": "__sysadmin__", "role": "system_admin", "exp": expire},
        settings.SECRET_KEY,
        algorithm="HS256",
    )


def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(_BEARER),
):
    """
    FastAPI dependency — raises 401 unless the bearer token is a valid
    system_admin JWT.  Use this on every admin-only endpoint.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required.",
        )
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=["HS256"],
        )
        if payload.get("role") != "system_admin":
            raise JWTError("not admin")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired admin token.",
        )
