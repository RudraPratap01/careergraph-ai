"""
Auth service — business logic for registration and login.

Why a service layer?
  Routes handle HTTP. Services handle business logic.
  This separation means you can call auth logic from tests,
  other services, or admin tools without going through HTTP.
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User, UserRole
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.utils.security import hash_password, verify_password, create_access_token


def register_user(request: RegisterRequest, db: Session) -> User:
    """
    Creates a new user account.

    Steps:
    1. Check if email is already taken.
    2. Hash the password — never store plaintext.
    3. Create the User record.
    4. Commit to database.
    5. Return the new User.
    """
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    new_user = User(
        email=request.email,
        full_name=request.full_name.strip(),
        hashed_password=hash_password(request.password),
        role=request.role,
        is_active=True,
        is_verified=False,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def login_user(request: LoginRequest, db: Session) -> TokenResponse:
    """
    Validates credentials and returns a JWT token.

    Security note:
      We return the same generic error whether the email doesn't exist
      or the password is wrong. This prevents user enumeration attacks.
      (An attacker shouldn't learn whether an email is registered.)
    """
    user = db.query(User).filter(User.email == request.email).first()

    # Same error for wrong email AND wrong password — intentional
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password.",
    )

    if not user:
        raise invalid_credentials

    if not verify_password(request.password, user.hashed_password):
        raise invalid_credentials

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Contact support.",
        )

    # Create JWT — 'sub' (subject) is the standard JWT claim for user identity
    token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
        }
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role=user.role,
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
    )

