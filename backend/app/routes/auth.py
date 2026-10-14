"""
Authentication routes: register and login.

Route → Schema validation → Service (business logic) → Response.
Routes don't contain business logic — that lives in services/.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    TokenResponse,
    UserPublic,
)
from app.services.auth_service import register_user, login_user
from app.utils.security import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account",
)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Registers a new student, alumni, or admin.

    Input validation happens automatically via Pydantic (RegisterRequest).
    Business logic lives in auth_service.register_user().
    """
    user = register_user(request, db)
    return RegisterResponse(
        message="Account created successfully.",
        user=UserPublic.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive a JWT token",
)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates credentials and returns a JWT token.
    Store this token in the frontend and send it as:
      Authorization: Bearer <token>
    on all protected requests.
    """
    return login_user(request, db)


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Get the currently authenticated user",
)
def me(current_user=Depends(get_current_user)):
    """
    Protected route — requires a valid JWT token.
    Returns the profile of the currently logged-in user.
    """
    return UserPublic.model_validate(current_user)
