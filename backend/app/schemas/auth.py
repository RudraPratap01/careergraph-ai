"""
Auth schemas — Pydantic models for request/response validation.

The key principle: DB models (SQLAlchemy) handle storage.
Schemas (Pydantic) handle API input/output validation.
Never return a DB model directly to the user —
always convert to a schema first to control what is exposed.
"""

from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from app.models.user import UserRole
import re


class RegisterRequest(BaseModel):
    """Validates incoming registration data."""
    email: EmailStr
    full_name: str
    password: str
    role: UserRole = UserRole.STUDENT

    @field_validator("full_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Full name must be at least 2 characters.")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        return v


class LoginRequest(BaseModel):
    """Validates incoming login data."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """What we return after successful login."""
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    user_id: int
    full_name: str


class UserPublic(BaseModel):
    """
    Safe representation of a user — excludes hashed_password.
    Use this whenever returning user data from any endpoint.
    """
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class RegisterResponse(BaseModel):
    message: str
    user: UserPublic
