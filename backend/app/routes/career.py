"""
Career routes — Phase 4: Skill gaps & career readiness.

GET /career/occupations          list the occupation catalog
GET /career/occupations/{key}    one occupation with its required skills
GET /career/gap-analysis         deterministic readiness analysis for the
                                 current user against a target occupation

Route → Schema validation → Service (business logic) → Response.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.data.occupations import get_occupation, list_occupations
from app.database.session import get_db
from app.models.profile import StudentProfile
from app.models.user import User, UserRole
from app.schemas.career import OccupationDetail, OccupationSummary, SkillGapResponse
from app.services.skill_gap_service import analyze_skill_gap, get_profile_skills
from app.utils.security import get_current_user

router = APIRouter(prefix="/career", tags=["Career Intelligence (Phase 4)"])


def _require_student(current_user: User) -> None:
    if current_user.role not in (UserRole.STUDENT, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Skill-gap analysis is only available for student accounts.",
        )


@router.get(
    "/occupations",
    response_model=List[OccupationSummary],
    summary="List the target-occupation catalog",
)
def list_all_occupations(current_user: User = Depends(get_current_user)):
    """Returns every curated target occupation with a short summary."""
    return list_occupations()


@router.get(
    "/occupations/{key}",
    response_model=OccupationDetail,
    summary="Get a single occupation with its required and optional skills",
)
def get_one_occupation(
    key: str,
    current_user: User = Depends(get_current_user),
):
    """Returns an occupation by key, name, or alias."""
    occupation = get_occupation(key)
    if not occupation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown occupation '{key}'.",
        )
    return OccupationDetail(
        key=occupation["key"],
        name=occupation["name"],
        category=occupation["category"],
        description=occupation["description"],
        required_skill_count=len(occupation.get("required_skills", [])),
        source=occupation.get("source", "curated"),
        required_skills=[r["name"] for r in occupation.get("required_skills", [])],
        optional_skills=[o["name"] for o in occupation.get("optional_skills", [])],
    )


@router.get(
    "/gap-analysis",
    response_model=SkillGapResponse,
    summary="Compute deterministic skill-gap and readiness for a target occupation",
)
def gap_analysis(
    occupation: Optional[str] = Query(
        None,
        description="Occupation key/name/alias. Defaults to your saved target role.",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Deterministic, explainable readiness analysis.

    - Uses the user's saved skill inventory (StudentProfile.skills).
    - Uses the requested occupation, otherwise the student's saved target_role.
    - Returns matched/missing required skills, bonus skills, unknown skills,
      a per-skill contribution breakdown, and an explanation.
    """
    _require_student(current_user)

    target = occupation
    source = "request"
    if not target:
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).first()
        target = profile.target_role if profile else None
        source = "profile.target_role"

    if not target:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "No target occupation selected. Set a target role on your profile "
                "or pass the 'occupation' query parameter."
            ),
        )

    result = analyze_skill_gap(get_profile_skills(db, current_user), target)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown occupation '{target}'.",
        )

    result.target_source = source
    return result
