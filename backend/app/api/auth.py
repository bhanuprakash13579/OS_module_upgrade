from collections import defaultdict
from datetime import timedelta, date
import time

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.auth import User
from app.schemas.auth import Token, UserOut, UserUpdatePassword
from app.services.auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_active_user,
)
import app.state as state

router = APIRouter()

# ── Login rate limiting (in-memory, prod mode only) ───────────────────────────
_login_attempts: dict[str, list[float]] = defaultdict(list)
_RATE_WINDOW_SECONDS = 300   # 5-minute window
_RATE_MAX_ATTEMPTS = 10      # max failed attempts per window

def _check_rate_limit(ip: str) -> bool:
    """Returns True if the IP is within allowed attempts. Only enforced in prod mode."""
    if not state.prod_mode:
        return True
    now = time.time()
    window_start = now - _RATE_WINDOW_SECONDS
    attempts = [t for t in _login_attempts[ip] if t > window_start]
    _login_attempts[ip] = attempts
    if len(attempts) >= _RATE_MAX_ATTEMPTS:
        return False
    _login_attempts[ip].append(now)
    return True

# ── Valid roles ───────────────────────────────────────────────────────────────
SDO_ROLES = {"SDO"}
ADJN_ROLES = {"DC", "AC"}


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=Token)
async def login_for_access_token(
    request: Request,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    client_ip = request.client.host if request.client else "unknown"
    if not _check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Please wait {_RATE_WINDOW_SECONDS // 60} minutes before trying again.",
        )

    user = db.query(User).filter(User.user_id == form_data.username).first()

    if not user or not verify_password(form_data.password, user.user_pwd):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.user_status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is CLOSED",
        )

    # Module-specific access check
    form = await request.form()
    module_type = (form.get("module_type") or "").lower()

    if module_type == "sdo":
        if user.user_role not in SDO_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access Denied: Role '{user.user_role}' cannot access the SDO Module.",
            )
    elif module_type == "adjudication":
        if user.user_role not in ADJN_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access Denied: Role '{user.user_role}' cannot access the Adjudication Module.",
            )

    access_token = create_access_token(
        data={"sub": user.user_id, "role": user.user_role},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer", "user": user}


# ── Current user ──────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserOut)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


# ── Change own password ───────────────────────────────────────────────────────

@router.post("/change-password")
def change_password(
    data: UserUpdatePassword,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Users can change their own password by supplying the old one."""
    if not verify_password(data.old_password, current_user.user_pwd):
        raise HTTPException(status_code=400, detail="Incorrect old password")
    current_user.user_pwd = get_password_hash(data.new_password)
    db.commit()
    return {"message": "Password updated successfully"}


# ── Close own account ─────────────────────────────────────────────────────────

@router.delete("/users/{user_id}")
def close_own_account(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Users can only soft-delete their own account."""
    if current_user.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You can only close your own account.",
        )
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.user_status = "CLOSED"
    user.closed_on = date.today()
    db.commit()
    return {"message": f"Account {user_id} closed successfully"}
