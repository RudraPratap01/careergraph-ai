"""
Career schemas — Pydantic models for Phase 4: Skill gaps & career readiness.

Separates DB models from API response models, consistent with the rest of the
project. The readiness score is deterministic and computed entirely in
``app/services/skill_gap_service.py`` — no LLM is involved.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class OccupationSummary(BaseModel):
    key: str
    name: str
    category: str
    description: str
    required_skill_count: int
    source: str = "curated"


class OccupationDetail(OccupationSummary):
    required_skills: List[str] = []
    optional_skills: List[str] = []


class SkillAssessment(BaseModel):
    """A single required (or bonus) skill judged against the user's inventory."""
    name: str
    category: Optional[str] = None
    weight: int = Field(..., ge=1, le=5)
    matched: bool
    user_level: Optional[str] = None
    rationale: str = ""


class SkillContribution(BaseModel):
    """Per-skill contribution to the readiness score, for explainability."""
    name: str
    weight: int
    matched: bool


class SkillGapRequest(BaseModel):
    occupation: Optional[str] = Field(
        None,
        description=(
            "Occupation key, name, or alias (e.g. 'backend-developer' or "
            "'Backend Developer'). Defaults to the student's saved target_role."
        ),
    )


class SkillGapResponse(BaseModel):
    occupation_key: str
    occupation_name: str
    occupation_category: str
    target_source: str = Field(
        ...,
        description="Where the occupation was taken from: 'request' or 'profile.target_role'.",
    )
    readiness_score: int = Field(..., ge=0, le=100)
    readiness_band: str
    matched_count: int
    required_count: int
    matched_skills: List[SkillAssessment] = []
    missing_skills: List[SkillAssessment] = []
    bonus_skills: List[SkillAssessment] = []
    missing_bonus_skills: List[SkillAssessment] = []
    unknown_skills: List[str] = []
    contributions: List[SkillContribution] = []
    explanation: str
    disclaimer: str
