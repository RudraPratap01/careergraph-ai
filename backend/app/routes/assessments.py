"""
Assessment routes — Phase 8: assessments.

GET  /assessments                                 catalogue of assessments
GET  /assessments/attempts                        your attempt history
GET  /assessments/{key}                           one assessment (no answers)
POST /assessments/{key}/start                     open a new attempt
POST /assessments/attempts/{id}/submit            grade an attempt
POST /assessments/attempts/{id}/confirm-skills    add evidenced skills to your profile

Route → Schema validation → Service (business logic) → Response.

Note the route order: the literal ``/attempts`` paths are declared before the
``/{key}`` path so a key can never swallow them.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User, UserRole
from app.schemas.assessment import (
    AssessmentAttemptResponse,
    AssessmentDetail,
    AssessmentResultResponse,
    AssessmentSubmitRequest,
    AssessmentSummary,
    AttemptStartResponse,
    ConfirmSkillsRequest,
    ConfirmSkillsResponse,
)
from app.services.assessment_service import (
    confirm_skills,
    get_catalog,
    grade_attempt,
    list_attempts,
    public_assessment,
    start_attempt,
)
from app.data.assessments import get_assessment
from app.utils.security import get_current_user

router = APIRouter(prefix="/assessments", tags=["Assessments (Phase 8)"])


def _require_student(current_user: User) -> None:
    if current_user.role not in (UserRole.STUDENT, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Assessments are only available for student accounts.",
        )


@router.get(
    "",
    response_model=List[AssessmentSummary],
    summary="List the available assessments",
)
def list_all_assessments(current_user: User = Depends(get_current_user)):
    """Returns every curated assessment with its skills and question count."""
    _require_student(current_user)
    return get_catalog()


@router.get(
    "/attempts",
    response_model=List[AssessmentAttemptResponse],
    summary="List your assessment attempts",
)
def my_attempts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_student(current_user)
    return list_attempts(db, current_user)


@router.get(
    "/{key}",
    response_model=AssessmentDetail,
    summary="Get one assessment's questions (answers are never included)",
)
def get_one_assessment(
    key: str,
    current_user: User = Depends(get_current_user),
):
    _require_student(current_user)
    record = get_assessment(key)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown assessment '{key}'.",
        )
    return public_assessment(record)


@router.post(
    "/{key}/start",
    response_model=AttemptStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new assessment attempt",
)
def start(
    key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Opens an attempt and returns the questions. Correct answers are never sent
    to the client — grading happens server-side on submit.
    """
    _require_student(current_user)
    result = start_attempt(db, current_user, key)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown assessment '{key}'.",
        )
    return result


@router.post(
    "/attempts/{attempt_id}/submit",
    response_model=AssessmentResultResponse,
    summary="Grade an assessment attempt",
)
def submit(
    attempt_id: int,
    request: AssessmentSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Grades the submitted answers deterministically and returns a per-question
    and per-skill breakdown. Unanswered questions count as incorrect.
    """
    _require_student(current_user)
    result = grade_attempt(db, current_user, attempt_id, request.answers)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment attempt not found.",
        )
    return result


@router.post(
    "/attempts/{attempt_id}/confirm-skills",
    response_model=ConfirmSkillsResponse,
    summary="Add skills evidenced by a passed attempt to your profile",
)
def confirm(
    attempt_id: int,
    request: ConfirmSkillsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Every requested skill must have been passed *in this attempt*. The endpoint
    never trusts the client's claim of evidence.
    """
    _require_student(current_user)
    result = confirm_skills(db, current_user, attempt_id, request.skills)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment attempt not found.",
        )
    return result
