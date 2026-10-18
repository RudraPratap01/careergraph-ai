"""
Mentorship request service — Phase 8.

Owns the request lifecycle and its authorization rules:

    student  creates a request for one alumni and may cancel it while it is pending
    alumni   accepts or declines requests addressed to them, subject to capacity
    admin    may view everything

Every rule is enforced server-side. Ownership is never inferred from the request
body: the acting user's identity always comes from the JWT.
"""

from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.mentorship import (
    STATUS_ACCEPTED,
    STATUS_CANCELLED,
    STATUS_DECLINED,
    STATUS_PENDING,
    MentorshipRequest,
)
from app.models.profile import AlumniProfile
from app.models.user import User, UserRole
from app.schemas.mentorship import MentorshipRequestResponse
from app.services.matching_service import list_mentor_matches


def accepted_mentee_count(db: Session, alumni_id: int) -> int:
    """How many students this alumni has already accepted."""
    return (
        db.query(func.count(MentorshipRequest.id))
        .filter(
            MentorshipRequest.alumni_id == alumni_id,
            MentorshipRequest.status == STATUS_ACCEPTED,
        )
        .scalar()
        or 0
    )


def serialize_request(request: MentorshipRequest) -> MentorshipRequestResponse:
    return MentorshipRequestResponse(
        id=request.id,
        student_id=request.student_id,
        student_name=request.student.full_name if request.student else None,
        alumni_id=request.alumni_id,
        alumni_name=request.alumni.full_name if request.alumni else None,
        message=request.message,
        status=request.status,
        match_score=request.match_score,
        created_at=request.created_at,
        updated_at=request.updated_at,
    )


def get_owned_request(
    db: Session, user: User, request_id: int
) -> Optional[MentorshipRequest]:
    """
    Returns a request the user is *party to* (as the student or the alumni).
    Anything else is invisible, so unrelated users get a 404 rather than a 403
    that would confirm the request exists.
    """
    return (
        db.query(MentorshipRequest)
        .filter(
            MentorshipRequest.id == request_id,
            (MentorshipRequest.student_id == user.id)
            | (MentorshipRequest.alumni_id == user.id),
        )
        .first()
    )


def _require_alumni_mentor(db: Session, alumni_user: User) -> AlumniProfile:
    if alumni_user.role != UserRole.ALUMNI:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mentorship can only be requested from an alumni account.",
        )
    profile = db.query(AlumniProfile).filter(AlumniProfile.user_id == alumni_user.id).first()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="That alumni has not set up a mentor profile yet.",
        )
    return profile


def create_request(
    db: Session, student: User, alumni_user_id: int, message: Optional[str]
) -> MentorshipRequestResponse:
    if alumni_user_id == student.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot request mentorship from yourself.",
        )

    alumni_user = (
        db.query(User)
        .filter(User.id == alumni_user_id, User.is_active == True)  # noqa: E712
        .first()
    )
    if alumni_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mentor not found.",
        )
    _require_alumni_mentor(db, alumni_user)

    existing = (
        db.query(MentorshipRequest)
        .filter(
            MentorshipRequest.student_id == student.id,
            MentorshipRequest.alumni_id == alumni_user_id,
            MentorshipRequest.status.in_((STATUS_PENDING, STATUS_ACCEPTED)),
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "You already have an accepted mentorship with this mentor."
                if existing.status == STATUS_ACCEPTED
                else "You already have a pending request with this mentor."
            ),
        )

    # Snapshot the deterministic match score so the request keeps its rationale.
    snapshot = next(
        (m for m in list_mentor_matches(db, student).matches if m.user_id == alumni_user_id),
        None,
    )

    request = MentorshipRequest(
        student_id=student.id,
        alumni_id=alumni_user_id,
        message=(message or "").strip() or None,
        status=STATUS_PENDING,
        match_score=snapshot.match_score if snapshot else None,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return serialize_request(request)


def list_requests(db: Session, user: User) -> List[MentorshipRequestResponse]:
    """Requests sent by a student, or addressed to an alumni. Admins see all."""
    query = db.query(MentorshipRequest)
    if user.role == UserRole.STUDENT:
        query = query.filter(MentorshipRequest.student_id == user.id)
    elif user.role == UserRole.ALUMNI:
        query = query.filter(MentorshipRequest.alumni_id == user.id)

    rows = query.order_by(
        MentorshipRequest.created_at.desc(), MentorshipRequest.id.desc()
    ).all()
    return [serialize_request(r) for r in rows]


def accept_request(db: Session, user: User, request_id: int) -> Optional[MentorshipRequestResponse]:
    request = get_owned_request(db, user, request_id)
    if request is None:
        return None
    if request.alumni_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the requested mentor can accept this request.",
        )
    if request.status != STATUS_PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"This request is already {request.status}.",
        )

    profile = _require_alumni_mentor(db, user)
    max_mentees = int(profile.max_mentees or 0)
    accepted = accepted_mentee_count(db, user.id)
    if accepted >= max_mentees:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"You have reached your mentee limit ({accepted}/{max_mentees}). "
                "Raise your limit on your profile to accept more students."
            ),
        )

    request.status = STATUS_ACCEPTED
    db.commit()
    db.refresh(request)
    return serialize_request(request)


def decline_request(db: Session, user: User, request_id: int) -> Optional[MentorshipRequestResponse]:
    request = get_owned_request(db, user, request_id)
    if request is None:
        return None
    if request.alumni_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the requested mentor can decline this request.",
        )
    if request.status != STATUS_PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"This request is already {request.status}.",
        )

    request.status = STATUS_DECLINED
    db.commit()
    db.refresh(request)
    return serialize_request(request)


def cancel_request(db: Session, user: User, request_id: int) -> Optional[MentorshipRequestResponse]:
    request = get_owned_request(db, user, request_id)
    if request is None:
        return None
    if request.student_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the student who sent this request can cancel it.",
        )
    if request.status != STATUS_PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"This request is already {request.status}.",
        )

    request.status = STATUS_CANCELLED
    db.commit()
    db.refresh(request)
    return serialize_request(request)
