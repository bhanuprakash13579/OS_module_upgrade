from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.auth import User
from app.security.passwords import pwd_context

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.user_status not in ("ACTIVE", "TEMP"):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_dc_ac_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Adjudication functions gated to DC and AC only."""
    if current_user.user_role not in ["DC", "AC"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requires DC or AC privileges"
        )
    return current_user


# ── SDO Module Guard ───────────────────────────────────────────────────────
SDO_ROLES = {"SDO"}

def get_sdo_user(current_user: User = Depends(get_current_active_user)) -> User:
    """SDO Module: SDO role only."""
    if current_user.user_role not in SDO_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: This operation is restricted to SDO module users"
        )
    return current_user


# ── Adjudication Module Guard ──────────────────────────────────────────────
ADJN_ROLES = {"DC", "AC"}

def get_adjn_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Adjudication Module: DC and AC only."""
    if current_user.user_role not in ADJN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: This operation is restricted to Adjudication module users"
        )
    return current_user
