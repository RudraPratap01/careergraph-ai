"""
Verification routes — Phase 6: GitHub verification & LinkedIn link.

POST   /verification/github                  verify (or re-verify) a GitHub account
GET    /verification/github                  the stored verification, if any
DELETE /verification/github                  unlink the GitHub account
POST   /verification/github/confirm-skills   add selected detected skills to the profile
POST   /verification/linkedin                store a self-declared LinkedIn URL
GET    /verification/linkedin                the stored LinkedIn link, if any
GET    /verification/status                  combined GitHub + LinkedIn status

Route → Schema validation → Service (business logic) → Response.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.schemas.verification import (
    GitHubConfirmRequest,
    GitHubConfirmResponse,
    GitHubDisconnectResponse,
    GitHubVerificationResponse,
    GitHubVerifyRequest,
    LinkedInLinkRequest,
    LinkedInLinkResponse,
    VerificationStatusResponse,
)
from app.services.github_service import (
    confirm_github_skills,
    disconnect_github,
    get_linkedin,
    get_stored_verification,
    get_verification_status,
    link_linkedin,
    verify_github_account,
)
from app.utils.security import get_current_user

router = APIRouter(prefix="/verification", tags=["Verification (Phase 6)"])


@router.post("/github", response_model=GitHubVerificationResponse)
def verify_github(
    payload: GitHubVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fetches the public GitHub account and its repositories, stores the analysis,
    and returns evidence-backed skill suggestions for the student to confirm.
    """
    return verify_github_account(current_user, payload.username, db)


@router.get("/github", response_model=GitHubVerificationResponse)
def read_github(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_stored_verification(current_user, db)


@router.delete("/github", response_model=GitHubDisconnectResponse)
def delete_github(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return disconnect_github(current_user, db)


@router.post("/github/confirm-skills", response_model=GitHubConfirmResponse)
def confirm_skills(
    payload: GitHubConfirmRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return confirm_github_skills(current_user, payload, db)


@router.post("/linkedin", response_model=LinkedInLinkResponse)
def save_linkedin(
    payload: LinkedInLinkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Stores a LinkedIn profile URL as a **self-declared, unverified** link.
    LinkedIn offers no public API for reading a member's profile.
    """
    return link_linkedin(current_user, payload, db)


@router.get("/linkedin", response_model=LinkedInLinkResponse)
def read_linkedin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_linkedin(current_user, db)


@router.get("/status", response_model=VerificationStatusResponse)
def read_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_verification_status(current_user, db)
