"""
Verification schemas — Phase 6: GitHub verification & LinkedIn link.

The project distinguishes three different levels of trust, and this module keeps
them explicit so the UI can never blur them:

* **GitHub account data** — fetched live from GitHub's public REST API, so it is
  genuinely verified at fetch time.
* **Inferred skills** — a deterministic heuristic over repository languages and
  topics. Each carries a confidence score and the repositories that evidence
  it. The student must confirm them before they reach the profile.
* **LinkedIn** — LinkedIn exposes no public API for reading a member's profile,
  so a LinkedIn URL is stored as *self-declared* and always reported with
  ``verified=False``. Nothing pretends otherwise.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class GitHubVerifyRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=39)


class GitHubAccount(BaseModel):
    username: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    profile_url: Optional[str] = None
    bio: Optional[str] = None
    public_repos: int = 0
    followers: int = 0
    following: int = 0
    account_created_at: Optional[datetime] = None
    account_age_days: Optional[int] = Field(
        None, description="Age of the GitHub account in days, derived from account_created_at."
    )


class GitHubLanguage(BaseModel):
    name: str
    count: int = Field(..., ge=1, description="Non-forked repositories using this language.")


class GitHubSkillEvidence(BaseModel):
    name: str
    category: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    repo_count: int = Field(..., ge=1)
    repos: List[str] = Field(default_factory=list, description="Up to 10 repository names.")
    stars: int = Field(0, ge=0)
    sources: List[str] = Field(default_factory=list, description="'language' and/or 'topic'.")
    proficiency: str = Field("beginner", pattern="^(beginner|intermediate|advanced)$")
    evidence: str = ""


class GitHubVerificationResponse(BaseModel):
    account: GitHubAccount
    languages: List[GitHubLanguage] = []
    skills: List[GitHubSkillEvidence] = []
    repos_analyzed: int = 0
    repos_truncated: bool = False
    forks_excluded: int = 0
    total_stars: int = 0
    target_role: Optional[str] = None
    relevant_to_target: List[str] = Field(
        default_factory=list,
        description="Detected skills that the student's target occupation also requires.",
    )
    explanation: str = ""
    disclaimer: str = ""
    verified_at: datetime
    source: str = "github"


class GitHubConfirmRequest(BaseModel):
    skills: List[str] = Field(
        ...,
        description="Canonical skills detected by the most recent verification.",
    )


class GitHubConfirmResponse(BaseModel):
    added: List[str] = []
    upgraded: List[str] = Field(
        default_factory=list,
        description="Skills that were already on the profile but were upgraded to evidence.",
    )
    already_present: List[str] = []
    skills: List[dict] = []
    message: str = ""


class LinkedInLinkRequest(BaseModel):
    url: str = Field(..., min_length=10, max_length=500)


class LinkedInLinkResponse(BaseModel):
    linkedin_url: str
    verified: bool = False
    note: str = (
        "LinkedIn does not provide a public API for reading a member's profile, "
        "so this link is self-declared and not verified."
    )


class VerificationStatusResponse(BaseModel):
    github: Optional[GitHubVerificationResponse] = None
    linkedin: Optional[LinkedInLinkResponse] = None


class GitHubDisconnectResponse(BaseModel):
    disconnected: bool
    message: str
