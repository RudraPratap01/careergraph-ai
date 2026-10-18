"""
Mentorship routes — Phase 8: alumni matching & mentorship requests.

GET  /mentorship/matches                ranked mentors for the current student
POST /mentorship/requests               a student requests mentorship
GET  /mentorship/requests               requests you sent (student) or received (alumni)
POST /mentorship/requests/{id}/accept   the requested alumni accepts
POST /mentorship/requests/{id}/decline  the requested alumni declines
POST /mentorship/requests/{id}/cancel   the requesting student cancels

Route → Schema validation → Service (business logic) → Response.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User, UserRole
from app.schemas.mentorship import (
    MentorshipActionResponse,
    MentorshipRequestCreate,
    MentorshipRequestResponse,
    MentorMatchListResponse,
)
from app.services.matching_service import list_mentor_matches
from app.services.mentorship_service import (
    accept_request,
    cancel_request,
    create_request,
    decline_request,
    list_requests,
)
from app.utils.security import get_current_user

router = APIRouter(prefix="/mentorship", tags=["Mentorship & Matching (Phase 8)"])


def _require_student(current_user: User) -> None:
    if current_user.role not in (UserRole.STUDENT, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mentor matching is only available for student accounts.",
        )


@router.get(
    "/matches",
    response_model=MentorMatchListResponse,
    summary="Rank alumni mentors for the current student",
)
def get_matches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Deterministic ranking with a per-factor breakdown. The score is a heuristic
    to order the list, not a prediction about any individual mentor.
    """
    _require_student(current_user)
    return list_mentor_matches(db, current_user)


@router.get(
    "/requests",
    response_model=List[MentorshipRequestResponse],
    summary="List your mentorship requests (sent or received)",
)
def get_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return list_requests(db, current_user)


@router.post(
    "/requests",
    response_model=MentorshipRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request mentorship from an alumni mentor",
)
def create(
    request: MentorshipRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Creates a pending request. A duplicate pending or accepted request for the
    same mentor returns ``409``.
    """
    _require_student(current_user)
    return create_request(db, current_user, request.alumni_user_id, request.message)


@router.post(
    "/requests/{request_id}/accept",
    response_model=MentorshipActionResponse,
    summary="Accept a mentorship request (mentor only, capacity enforced)",
)
def accept(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = accept_request(db, current_user, request_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentorship request not found.",
        )
    return MentorshipActionResponse(message="Mentorship request accepted.", request=result)


@router.post(
    "/requests/{request_id}/decline",
    response_model=MentorshipActionResponse,
    summary="Decline a mentorship request (mentor only)",
)
def decline(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = decline_request(db, current_user, request_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentorship request not found.",
        )
    return MentorshipActionResponse(message="Mentorship request declined.", request=result)


@router.post(
    "/requests/{request_id}/cancel",
    response_model=MentorshipActionResponse,
    summary="Cancel your own pending mentorship request (student only)",
)
def cancel(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = cancel_request(db, current_user, request_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentorship request not found.",
        )
    return MentorshipActionResponse(message="Mentorship request cancelled.", request=result)
