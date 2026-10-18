"""
Profile schemas — Pydantic models for student and alumni profile validation.

Phase 2: User Profiles
Follows the project's principle of separating DB models from API response models.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.user import UserRole


class SkillItem(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    level: str = Field("intermediate", pattern="^(beginner|intermediate|advanced)$")
    source: str = Field(
        "self",
        pattern="^(self|resume|assessment)$",
        description=(
            "Where the skill came from: self-reported ('self'), parsed from a "
            "resume ('resume'), or evidenced by a passed assessment ('assessment')."
        ),
    )


# ─── Student Profile ──────────────────────────────────────────────────────────

class StudentProfileBase(BaseModel):
    college: Optional[str] = None
    degree: Optional[str] = None
    current_year: Optional[int] = Field(None, ge=1, le=5)
    graduation_year: Optional[int] = Field(None, ge=2020, le=2035)
    cgpa: Optional[float] = Field(None, ge=0.0, le=10.0)
    target_role: Optional[str] = None
    target_timeline_months: Optional[int] = Field(6, ge=1, le=48)
    bio: Optional[str] = None
    github_username: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    skills: List[SkillItem] = []


class StudentProfileUpdate(StudentProfileBase):
    pass


class StudentProfileResponse(StudentProfileBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Alumni Profile ───────────────────────────────────────────────────────────

class AlumniProfileBase(BaseModel):
    company: Optional[str] = None
    job_title: Optional[str] = None
    years_of_experience: Optional[int] = Field(0, ge=0, le=50)
    college: Optional[str] = None
    graduation_year: Optional[int] = Field(None, ge=1970, le=2030)
    expertise_areas: List[str] = []
    bio: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_username: Optional[str] = None
    meeting_link: Optional[str] = None
    is_available_for_mentoring: bool = True
    max_mentees: int = Field(3, ge=1, le=20)


class AlumniProfileUpdate(AlumniProfileBase):
    pass


class AlumniProfileResponse(AlumniProfileBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Combined Profile & Mentors ───────────────────────────────────────────────

class CurrentUserProfileResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    completion_percentage: int
    student_profile: Optional[StudentProfileResponse] = None
    alumni_profile: Optional[AlumniProfileResponse] = None

    model_config = {"from_attributes": True}


class AlumniMentorCard(BaseModel):
    user_id: int
    full_name: str
    email: str
    company: Optional[str] = None
    job_title: Optional[str] = None
    years_of_experience: Optional[int] = 0
    college: Optional[str] = None
    expertise_areas: List[str] = []
    bio: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_username: Optional[str] = None
    is_available_for_mentoring: bool = True
    meeting_link: Optional[str] = None

    model_config = {"from_attributes": True}
