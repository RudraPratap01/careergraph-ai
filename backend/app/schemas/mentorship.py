"""
Mentorship schemas — Phase 8: alumni matching.

The match score is a deterministic, weighted ranking heuristic. Every factor
that contributes to it is returned so the ranking can be audited — and the
response carries a disclaimer stating it is not a promise of a good match.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class MatchFactor(BaseModel):
    key: str
    label: str
    weight: int = Field(..., ge=0, description="Maximum points this factor can award.")
    earned: int = Field(..., ge=0, description="Points actually awarded.")
    detail: str = ""


class MentorMatch(BaseModel):
    user_id: int
    full_name: str
    company: Optional[str] = None
    job_title: Optional[str] = None
    years_of_experience: int = 0
    college: Optional[str] = None
    expertise_areas: List[str] = []
    bio: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_username: Optional[str] = None
    meeting_link: Optional[str] = None

    is_available_for_mentoring: bool = True
    max_mentees: int = 0
    accepted_mentees: int = 0
    remaining_capacity: int = 0

    match_score: int = Field(..., ge=0, le=100)
    match_band: str
    overlap_skills: List[str] = []
    factors: List[MatchFactor] = []

    request_status: Optional[str] = Field(
        None,
        description="Your existing request status with this mentor, if any.",
    )


class MentorMatchListResponse(BaseModel):
    target_occupation: Optional[str] = None
    missing_skills: List[str] = []
    matches: List[MentorMatch] = []
    explanation: str = ""
    disclaimer: str = ""


class MentorshipRequestCreate(BaseModel):
    alumni_user_id: int = Field(..., gt=0)
    message: Optional[str] = Field(None, max_length=1000)


class MentorshipRequestResponse(BaseModel):
    id: int
    student_id: int
    student_name: Optional[str] = None
    alumni_id: int
    alumni_name: Optional[str] = None
    message: Optional[str] = None
    status: str
    match_score: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class MentorshipActionResponse(BaseModel):
    message: str
    request: MentorshipRequestResponse
