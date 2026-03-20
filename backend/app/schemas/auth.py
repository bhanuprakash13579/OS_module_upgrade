from typing import Optional, List
from datetime import date
from pydantic import BaseModel


class UserOut(BaseModel):
    id: int
    user_name: str
    user_desig: Optional[str] = None
    user_id: str
    user_role: str
    user_status: str
    created_on: Optional[date] = None
    created_by: Optional[str] = None
    closed_on: Optional[date] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Login response — includes token + user object so frontend knows role immediately."""
    access_token: str
    token_type: str
    user: UserOut


class TokenData(BaseModel):
    user_id: Optional[str] = None


class UserBase(BaseModel):
    user_name: str
    user_desig: Optional[str] = None
    user_id: str
    user_role: str
    user_status: str = "ACTIVE"


class UserCreate(UserBase):
    user_pwd: str


class UserUpdatePassword(BaseModel):
    old_password: str
    new_password: str
