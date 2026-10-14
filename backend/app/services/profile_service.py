"""
Profile service — business logic for student and alumni user profiles.

Phase 2: User Profiles
Provides profile calculation, upserting, retrieval, and mentor listing.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User, UserRole
from app.models.profile import StudentProfile, AlumniProfile
from app.schemas.profile import (
    StudentProfileUpdate,
    StudentProfileResponse,
    AlumniProfileUpdate,
    AlumniProfileResponse,
    CurrentUserProfileResponse,
    AlumniMentorCard,
)


def calculate_student_completion(profile: Optional[StudentProfile]) -> int:
    """Calculates student profile completion score as a percentage (0-100)."""
    if not profile:
        return 0

    checks = [
        bool(profile.college and profile.college.strip()),
        bool(profile.degree and profile.degree.strip()),
        bool(profile.graduation_year),
        bool(profile.target_role and profile.target_role.strip()),
        bool(profile.skills and len(profile.skills) > 0),
        bool(profile.bio and profile.bio.strip()),
        bool((profile.github_username and profile.github_username.strip()) or 
             (profile.linkedin_url and profile.linkedin_url.strip())),
    ]
    completed = sum(1 for c in checks if c)
    return int((completed / len(checks)) * 100)


def calculate_alumni_completion(profile: Optional[AlumniProfile]) -> int:
    """Calculates alumni profile completion score as a percentage (0-100)."""
    if not profile:
        return 0

    checks = [
        bool(profile.company and profile.company.strip()),
        bool(profile.job_title and profile.job_title.strip()),
        bool(profile.years_of_experience and profile.years_of_experience > 0),
        bool(profile.expertise_areas and len(profile.expertise_areas) > 0),
        bool(profile.bio and profile.bio.strip()),
        bool(profile.linkedin_url and profile.linkedin_url.strip()),
    ]
    completed = sum(1 for c in checks if c)
    return int((completed / len(checks)) * 100)


def get_current_user_profile(user: User, db: Session) -> CurrentUserProfileResponse:
    """Fetches user and their corresponding profile with completion metric."""
    student_resp = None
    alumni_resp = None
    completion = 0

    if user.role == UserRole.STUDENT:
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
        if profile:
            student_resp = StudentProfileResponse.model_validate(profile)
        completion = calculate_student_completion(profile)

    elif user.role == UserRole.ALUMNI:
        profile = db.query(AlumniProfile).filter(AlumniProfile.user_id == user.id).first()
        if profile:
            alumni_resp = AlumniProfileResponse.model_validate(profile)
        completion = calculate_alumni_completion(profile)

    return CurrentUserProfileResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        completion_percentage=completion,
        student_profile=student_resp,
        alumni_profile=alumni_resp,
    )


def upsert_student_profile(
    user: User,
    data: StudentProfileUpdate,
    db: Session,
) -> StudentProfileResponse:
    """Creates or updates a student profile."""
    if user.role not in [UserRole.STUDENT, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can update a student profile.",
        )

    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()

    # Convert Pydantic skill items to dicts for JSON storage
    skills_data = [s.model_dump() for s in data.skills] if data.skills else []

    if profile is None:
        profile = StudentProfile(
            user_id=user.id,
            college=data.college,
            degree=data.degree,
            current_year=data.current_year,
            graduation_year=data.graduation_year,
            cgpa=data.cgpa,
            target_role=data.target_role,
            target_timeline_months=data.target_timeline_months,
            bio=data.bio,
            github_username=data.github_username,
            linkedin_url=data.linkedin_url,
            portfolio_url=data.portfolio_url,
            skills=skills_data,
        )
        db.add(profile)
    else:
        profile.college = data.college
        profile.degree = data.degree
        profile.current_year = data.current_year
        profile.graduation_year = data.graduation_year
        profile.cgpa = data.cgpa
        profile.target_role = data.target_role
        profile.target_timeline_months = data.target_timeline_months
        profile.bio = data.bio
        profile.github_username = data.github_username
        profile.linkedin_url = data.linkedin_url
        profile.portfolio_url = data.portfolio_url
        profile.skills = skills_data

    db.commit()
    db.refresh(profile)
    return StudentProfileResponse.model_validate(profile)


def upsert_alumni_profile(
    user: User,
    data: AlumniProfileUpdate,
    db: Session,
) -> AlumniProfileResponse:
    """Creates or updates an alumni mentor profile."""
    if user.role not in [UserRole.ALUMNI, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only alumni can update an alumni profile.",
        )

    profile = db.query(AlumniProfile).filter(AlumniProfile.user_id == user.id).first()

    if profile is None:
        profile = AlumniProfile(
            user_id=user.id,
            company=data.company,
            job_title=data.job_title,
            years_of_experience=data.years_of_experience,
            college=data.college,
            graduation_year=data.graduation_year,
            expertise_areas=data.expertise_areas or [],
            bio=data.bio,
            linkedin_url=data.linkedin_url,
            github_username=data.github_username,
            meeting_link=data.meeting_link,
            is_available_for_mentoring=data.is_available_for_mentoring,
            max_mentees=data.max_mentees,
        )
        db.add(profile)
    else:
        profile.company = data.company
        profile.job_title = data.job_title
        profile.years_of_experience = data.years_of_experience
        profile.college = data.college
        profile.graduation_year = data.graduation_year
        profile.expertise_areas = data.expertise_areas or []
        profile.bio = data.bio
        profile.linkedin_url = data.linkedin_url
        profile.github_username = data.github_username
        profile.meeting_link = data.meeting_link
        profile.is_available_for_mentoring = data.is_available_for_mentoring
        profile.max_mentees = data.max_mentees

    db.commit()
    db.refresh(profile)
    return AlumniProfileResponse.model_validate(profile)


def get_public_profile(user_id: int, db: Session) -> Dict[str, Any]:
    """Retrieves a safe public view of any user and their profile."""
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found or inactive.",
        )

    response: Dict[str, Any] = {
        "id": user.id,
        "full_name": user.full_name,
        "role": user.role.value,
        "created_at": user.created_at,
    }

    if user.role == UserRole.STUDENT and user.student_profile:
        response["profile"] = StudentProfileResponse.model_validate(user.student_profile)
    elif user.role == UserRole.ALUMNI and user.alumni_profile:
        response["profile"] = AlumniProfileResponse.model_validate(user.alumni_profile)
    else:
        response["profile"] = None

    return response


def list_alumni_mentors(db: Session, expertise: Optional[str] = None) -> List[AlumniMentorCard]:
    """Lists available alumni mentors for student networking & guidance."""
    query = (
        db.query(AlumniProfile, User)
        .join(User, AlumniProfile.user_id == User.id)
        .filter(User.is_active == True)
        .filter(AlumniProfile.is_available_for_mentoring == True)
    )

    results = query.all()
    mentors: List[AlumniMentorCard] = []

    for profile, user in results:
        # If expertise filter given, check case-insensitive match in list
        if expertise:
            areas = [a.lower() for a in (profile.expertise_areas or [])]
            if not any(expertise.lower() in a for a in areas):
                continue

        mentors.append(
            AlumniMentorCard(
                user_id=user.id,
                full_name=user.full_name,
                email=user.email,
                company=profile.company,
                job_title=profile.job_title,
                years_of_experience=profile.years_of_experience or 0,
                college=profile.college,
                expertise_areas=profile.expertise_areas or [],
                bio=profile.bio,
                linkedin_url=profile.linkedin_url,
                github_username=profile.github_username,
                is_available_for_mentoring=profile.is_available_for_mentoring,
                meeting_link=profile.meeting_link,
            )
        )

    return mentors
