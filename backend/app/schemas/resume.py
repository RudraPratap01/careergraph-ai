"""
Resume schemas — Pydantic models for resume upload, parsing, confidence/evidence, and student review.

Phase 3: Resume Intelligence
Follows the project's principle of separating DB models from API response models.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class ExtractedSkill(BaseModel):
    name: str
    normalized_name: str
    category: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: str
    proficiency: str = Field("intermediate", pattern="^(beginner|intermediate|advanced)$")


class ResumeUploadResponse(BaseModel):
    resume_id: int
    filename: str
    file_type: str
    file_size_bytes: int
    extracted_skills_count: int
    extracted_skills: List[ExtractedSkill]
    raw_text_snippet: str
    status: str
    created_at: datetime


class ResumeDetailResponse(BaseModel):
    id: int
    user_id: int
    filename: str
    file_type: str
    file_size_bytes: int
    extracted_skills: List[ExtractedSkill]
    raw_text: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConfirmSkillItem(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    level: str = Field("intermediate", pattern="^(beginner|intermediate|advanced)$")
    category: Optional[str] = None
    source: str = Field(
        "resume",
        pattern="^(resume|self)$",
        description=(
            "Provenance to store for this reviewed skill. 'resume' marks a skill "
            "matched by the resume, while 'self' keeps a skill that was already "
            "on the profile as self-reported. Evidence sources (assessment, "
            "github) cannot be claimed through this request."
        ),
    )


class ConfirmSkillsRequest(BaseModel):
    resume_id: Optional[int] = None
    skills: List[ConfirmSkillItem]


class ConfirmSkillsResponse(BaseModel):
    message: str
    total_confirmed_skills: int
    synced_to_profile: bool
    skills: List[ConfirmSkillItem]
