"""
Phase 7 routes - grounded career intelligence.

POST /intelligence/ask      ask a career-learning question grounded in the
                           current student's deterministic gap/roadmap context
                           and the curated knowledge base
GET  /intelligence/status   configuration/corpus status without credentials

The route is authenticated and student-scoped. It never accepts a user ID or
resume payload, so one account cannot request another account's context.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.session import get_db
from app.models.user import User, UserRole
from app.schemas.career_intelligence import AdvisorRequest, AdvisorResponse, AdvisorStatus
from app.services.career_intelligence_service import (
    OpenRouterClient,
    UnknownOccupationError,
    answer_career_question,
    build_llm_client,
    get_status,
)
from app.utils.security import get_current_user

router = APIRouter(prefix="/intelligence", tags=["Career Intelligence (Phase 7)"])


def get_llm_client_dependency() -> Optional[OpenRouterClient]:
    """FastAPI dependency; tests override this with a deterministic fake."""
    return build_llm_client(get_settings())


def _require_student(current_user: User) -> None:
    if current_user.role not in (UserRole.STUDENT, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Career intelligence is only available for student accounts.",
        )


@router.get(
    "/status",
    response_model=AdvisorStatus,
    summary="Show grounded-advisor configuration and corpus status",
)
def advisor_status(current_user: User = Depends(get_current_user)):
    """
    Returns whether an LLM is configured and how the local corpus is indexed.

    The API key itself is never returned. ``llm_configured=false`` means the
    deterministic local fallback is active.
    """
    return get_status()


@router.post(
    "/ask",
    response_model=AdvisorResponse,
    summary="Ask a grounded career-learning question",
)
def ask_advisor(
    data: AdvisorRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    llm_client: Optional[OpenRouterClient] = Depends(get_llm_client_dependency),
):
    """
    Answers using the current user's profile, deterministic gap and roadmap
    plan, plus retrieved curated sources. If no LLM key is configured, or the
    configured provider is unavailable/invalid, a deterministic extractive
    answer is returned and ``mode`` reports that honestly.
    """
    _require_student(current_user)
    try:
        return answer_career_question(
            db,
            current_user,
            data.question,
            occupation=data.occupation,
            llm_client=llm_client,
        )
    except UnknownOccupationError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown occupation '{data.occupation}'.",
        )
