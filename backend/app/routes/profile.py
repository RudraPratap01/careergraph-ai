"""
Profile routes — endpoints for student and alumni profile management.

Phase 2: User Profiles
Route → Schema validation → Service (business logic) → Response.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.utils.security import get_current_user
from app.schemas.profile import (
    StudentProfileUpdate,
    StudentProfileResponse,
    AlumniProfileUpdate,
    AlumniProfileResponse,
    CurrentUserProfileResponse,
    AlumniMentorCard,
)
from app.services.profile_service import (
    get_current_user_profile,
    upsert_student_profile,
    upsert_alumni_profile,
    get_public_profile,
    list_alumni_mentors,
)

router = APIRouter(tags=["Profiles"])


@router.get(
    "/profile/me",
    response_model=CurrentUserProfileResponse,
    summary="Get current user's complete profile with completion score",
)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the full profile for the currently logged-in user,
    including completion percentage and role-specific details.
    """
    return get_current_user_profile(current_user, db)


@router.put(
    "/profile/student",
    response_model=StudentProfileResponse,
    summary="Create or update current student's profile",
)
def update_student(
    data: StudentProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upserts the student profile (education, target role, timeline, self-reported skills, links).
    """
    return upsert_student_profile(current_user, data, db)


@router.put(
    "/profile/alumni",
    response_model=AlumniProfileResponse,
    summary="Create or update current alumni's profile",
)
def update_alumni(
    data: AlumniProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upserts the alumni mentor profile (company, title, experience, expertise, availability).
    """
    return upsert_alumni_profile(current_user, data, db)


@router.get(
    "/profile/{user_id}",
    summary="Get public profile for a user",
)
def get_user_public_profile(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Returns safe public details of a student or alumni member.
    """
    return get_public_profile(user_id, db)


@router.get(
    "/alumni",
    response_model=List[AlumniMentorCard],
    summary="List available alumni mentors",
)
def get_mentors(
    expertise: Optional[str] = Query(None, description="Filter mentors by expertise keyword"),
    db: Session = Depends(get_db),
):
    """
    Returns active alumni open to mentoring, optionally filtered by expertise.
    """
    return list_alumni_mentors(db, expertise)
