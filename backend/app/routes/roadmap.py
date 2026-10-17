"""
Roadmap routes — Phase 5: learning roadmap generation & progress.

POST /roadmap/generate            generate (or reuse) the active roadmap
GET  /roadmap                     current active roadmap for the user
GET  /roadmap/{roadmap_id}        a specific roadmap you own
GET  /roadmap/{roadmap_id}/explanations
POST /roadmap/{roadmap_id}/steps  update one step's progress
POST /roadmap/refresh             regenerate from current profile + target role

Route → Schema validation → Service (business logic) → Response.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.data.occupations import get_occupation
from app.database.session import get_db
from app.models.profile import StudentProfile
from app.models.user import User, UserRole
from app.schemas.roadmap import (
    RoadmapGenerateRequest,
    RoadmapResponse,
    RoadmapStepUpdateRequest,
    RoadmapStepUpdateResponse,
)
from app.services.graph_service import get_graph
from app.services.roadmap_service import (
    generate_roadmap,
    get_active_roadmap,
    get_roadmap_by_id,
    serialize_roadmap,
    update_step_state,
)
from app.utils.security import get_current_user

router = APIRouter(prefix="/roadmap", tags=["Learning Roadmap (Phase 5)"])


class StepExplanation(BaseModel):
    position: int
    skill: str
    reason: str
    prerequisites: List[str] = []


def _require_student(current_user: User) -> None:
    if current_user.role not in (UserRole.STUDENT, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Learning roadmaps are only available for student accounts.",
        )


def _resolve_target(db: Session, user: User, occupation: Optional[str]) -> tuple:
    """Returns (occupation_name, target_source) or raises 400."""
    if occupation:
        return occupation, "request"
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user.id).first()
    if profile and profile.target_role:
        return profile.target_role, "profile.target_role"
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=(
            "No target occupation selected. Set a target role on your profile "
            "or pass an 'occupation' value."
        ),
    )


@router.post(
    "/generate",
    response_model=RoadmapResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a prerequisite-aware learning roadmap",
)
def create_roadmap(
    request: RoadmapGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generates a roadmap from verified skills, the target occupation, and the
    skill-dependency graph. Existing active roadmap progress for the same
    occupation is preserved.
    """
    _require_student(current_user)

    target, source = _resolve_target(db, current_user, request.occupation)
    occupation = get_occupation(target)
    if not occupation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown occupation '{target}'.",
        )

    existing = get_active_roadmap(db, current_user)
    if existing and not request.regenerate and existing.occupation_key == occupation["key"]:
        return serialize_roadmap(existing)

    preserve = existing if (existing and existing.occupation_key == occupation["key"]) else None
    roadmap = generate_roadmap(db, current_user, get_graph(), target, source, preserve_progress_from=preserve)
    return serialize_roadmap(roadmap)


@router.get(
    "",
    response_model=RoadmapResponse,
    summary="Get the current active roadmap",
)
def get_current(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_student(current_user)
    roadmap = get_active_roadmap(db, current_user)
    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No roadmap yet. Generate one from your target occupation and skills.",
        )
    return serialize_roadmap(roadmap)


@router.post(
    "/refresh",
    response_model=RoadmapResponse,
    summary="Regenerate the roadmap from current profile skills & target role",
)
def refresh_roadmap(
    occupation: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Recomputes the roadmap after skills or the target occupation have changed.
    Progress is preserved for steps that still exist.
    """
    _require_student(current_user)

    existing = get_active_roadmap(db, current_user)
    explicit = occupation
    if explicit:
        target, source = explicit, "request"
    elif existing:
        target, source = existing.occupation_key, existing.target_source
    else:
        target, source = _resolve_target(db, current_user, None)

    occupation_record = get_occupation(target)
    if not occupation_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown occupation '{target}'.",
        )

    preserve = existing if (existing and existing.occupation_key == occupation_record["key"]) else None
    roadmap = generate_roadmap(db, current_user, get_graph(), target, source, preserve_progress_from=preserve)
    return serialize_roadmap(roadmap)


@router.get(
    "/{roadmap_id}",
    response_model=RoadmapResponse,
    summary="Get one of your roadmaps by id",
)
def get_one(
    roadmap_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_student(current_user)
    roadmap = get_roadmap_by_id(db, current_user, roadmap_id)
    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found.",
        )
    return serialize_roadmap(roadmap)


@router.get(
    "/{roadmap_id}/explanations",
    response_model=List[StepExplanation],
    summary="Get the per-step explanations for a roadmap you own",
)
def get_explanations(
    roadmap_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_student(current_user)
    roadmap = get_roadmap_by_id(db, current_user, roadmap_id)
    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found.",
        )
    return [
        StepExplanation(
            position=s["position"],
            skill=s["skill"],
            reason=s.get("reason", ""),
            prerequisites=s.get("prerequisites", []),
        )
        for s in (roadmap.steps or [])
    ]


@router.post(
    "/{roadmap_id}/steps",
    response_model=RoadmapStepUpdateResponse,
    summary="Update the progress state of one roadmap step",
)
def update_step(
    roadmap_id: int,
    request: RoadmapStepUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Marks a step as pending, in_progress, or completed.

    Returns 404 if the roadmap is not yours or the skill is not a step in it.
    """
    _require_student(current_user)
    roadmap = get_roadmap_by_id(db, current_user, roadmap_id)
    if not roadmap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Roadmap not found.",
        )

    result = update_step_state(db, current_user, roadmap, request.skill, request.state)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"'{request.skill}' is not a step in this roadmap.",
        )
    return result
