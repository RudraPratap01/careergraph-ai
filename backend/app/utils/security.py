"""
Security utilities: password hashing and JWT token management.

Why bcrypt?
  bcrypt is slow by design — it makes brute-force attacks expensive.
  We never store plaintext passwords.

Why JWT?
  JSON Web Tokens let us store user identity in the token itself.
  The server doesn't need to look up every request in the DB.
  Instead, it verifies the token signature using the SECRET_KEY.

Token structure:
  Header.Payload.Signature
  Payload contains: user_id, email, role, expiry
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.session import get_db

import bcrypt

settings = get_settings()

# HTTP Bearer scheme — allows pasting raw JWT Bearer token in Swagger UI Authorize dialog
http_bearer = HTTPBearer(auto_error=False, description="Enter your JWT Bearer token")
oauth2_scheme = http_bearer  # Backward-compatible alias


def hash_password(plain_password: str) -> str:
    """Converts a plaintext password to a bcrypt hash."""
    pwd_bytes = plain_password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Checks whether a plaintext password matches the stored hash."""
    pwd_bytes = plain_password.encode("utf-8")[:72]
    return bcrypt.checkpw(pwd_bytes, hashed_password.encode("utf-8"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a signed JWT token.
    'data' should contain: sub (user_id), email, role.
    The token expires after ACCESS_TOKEN_EXPIRE_MINUTES by default.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decodes and verifies a JWT token.
    Raises HTTPException 401 if the token is invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception


def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer),
    db: Session = Depends(get_db),
):
    """
    FastAPI dependency: extracts and validates the current user from JWT.
    Use this on any route that requires authentication.

    Example:
        @router.get("/profile")
        def get_profile(current_user = Depends(get_current_user)):
            ...
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if auth is None or not auth.credentials:
        raise credentials_exception

    from app.models.user import User  # local import to avoid circular deps

    payload = decode_access_token(auth.credentials)

    # The "sub" claim must be a numeric user id. A malformed token (e.g. a valid
    # signature but a non-numeric sub) must return 401, never a 500.
    raw_sub = payload.get("sub")
    try:
        user_id = int(raw_sub)
    except (TypeError, ValueError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account deactivated.",
        )
    return user


def require_role(*roles: str):
    """
    FastAPI dependency factory for role-based access control.

    Usage:
        @router.get("/admin/users")
        def list_users(current_user = Depends(require_role("admin"))):
            ...
    """
    def role_checker(current_user=Depends(get_current_user)):
        # UserRole is a str-Enum, but normalise defensively so that plain string
        # roles are compared correctly regardless of how the value was produced.
        role_value = getattr(current_user.role, "value", current_user.role)
        if role_value not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {list(roles)}",
            )
        return current_user
    return role_checker
