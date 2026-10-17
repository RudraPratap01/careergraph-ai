"""
Roadmap schemas — Phase 5: skill dependency graph & personalized learning roadmap.

Response models separate DB storage from the API surface, consistent with the
rest of the project.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PrerequisiteItem(BaseModel):
    skill: str
    depth: int = Field(..., ge=1)
    category: Optional[str] = None
    rationale: str = ""
    source: str = "curated"


class SkillDependencyResponse(BaseModel):
    skill: str
    known: bool
    category: Optional[str] = None
    has_prerequisites: bool = False
    prerequisites: List[PrerequisiteItem] = []
    dependents: List[PrerequisiteItem] = []
    unknown_related: List[str] = []


class RoadmapGenerateRequest(BaseModel):
    occupation: Optional[str] = Field(
        None,
        description="Occupation key/name/alias. Defaults to the saved target role.",
    )
    regenerate: bool = Field(
        True,
        description="When False, returns the existing active roadmap if one exists.",
    )


class RoadmapStep(BaseModel):
    position: int = Field(..., ge=1)
    skill: str
    category: Optional[str] = None
    depth: int = Field(0, ge=0, description="0 = required by the role; >=1 = prerequisite depth.")
    status: str = Field("pending", pattern="^(pending|in_progress|completed)$")
    is_target_skill: bool = False
    is_mastered: bool = False
    prerequisites: List[str] = []
    reason: str = ""


class RoadmapProgress(BaseModel):
    total_steps: int
    completed_steps: int
    in_progress_steps: int
    percent_complete: int = Field(..., ge=0, le=100)


class RoadmapResponse(BaseModel):
    id: int
    user_id: int
    occupation_key: str
    occupation_name: str
    occupation_category: Optional[str] = None
    target_source: str
    graph_backend: str
    is_partial: bool
    notes: Optional[str] = None
    status: str
    steps: List[RoadmapStep]
    possessed_skills: List[str] = []
    progress: RoadmapProgress
    next_action: Optional[str] = None
    explanation: str = ""
    disclaimer: str = ""
    created_at: datetime
    updated_at: datetime


class RoadmapStepUpdateRequest(BaseModel):
    skill: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., pattern="^(pending|in_progress|completed)$")


class RoadmapStepUpdateResponse(BaseModel):
    message: str
    step: RoadmapStep
    progress: RoadmapProgress
    next_action: Optional[str] = None
