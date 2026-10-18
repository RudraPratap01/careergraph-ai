"""
Assessment schemas — Phase 8: assessments.

Two views of a question exist on purpose:

* ``AssessmentQuestion`` — the *public* view. It deliberately has no answer
  field, so a correct answer can never leak to the client before submission.
* ``QuestionResult`` — the post-submission view, which reveals the correct
  answer and the explanation for review.

Response models separate DB storage from the API surface, consistent with the
rest of the project.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ─── Catalog ──────────────────────────────────────────────────────────────────
class AssessmentSummary(BaseModel):
    key: str
    name: str
    description: str
    skills: List[str] = []
    question_count: int
    pass_threshold: int
    source: str = "curated"


class AssessmentQuestion(BaseModel):
    id: str
    skill: str
    difficulty: str
    prompt: str
    options: List[str]


class AssessmentDetail(AssessmentSummary):
    questions: List[AssessmentQuestion] = []


# ─── Attempts ─────────────────────────────────────────────────────────────────
class SkillEvidence(BaseModel):
    skill: str
    category: Optional[str] = None
    correct: int
    total: int
    score_percent: int = Field(..., ge=0, le=100)
    passed: bool
    eligible_for_evidence: bool


class AssessmentAttemptResponse(BaseModel):
    id: int
    user_id: int
    assessment_key: str
    assessment_name: str
    status: str
    score_percent: Optional[int] = None
    passed: Optional[bool] = None
    correct_count: Optional[int] = None
    total_count: Optional[int] = None
    skills: List[SkillEvidence] = []
    passed_skills: List[str] = []
    started_at: datetime
    completed_at: Optional[datetime] = None


class AttemptStartResponse(BaseModel):
    attempt: AssessmentAttemptResponse
    questions: List[AssessmentQuestion]


class AnswerItem(BaseModel):
    question_id: str = Field(..., min_length=1)
    chosen_index: int = Field(..., ge=0)


class AssessmentSubmitRequest(BaseModel):
    answers: List[AnswerItem] = []


class QuestionResult(BaseModel):
    question_id: str
    skill: str
    correct: bool
    chosen_index: Optional[int] = None
    correct_index: int
    explanation: str


class AssessmentResultResponse(BaseModel):
    attempt: AssessmentAttemptResponse
    results: List[QuestionResult] = []
    suggested_skills: List[str] = []
    explanation: str = ""
    disclaimer: str = ""


# ─── Turning a pass into profile evidence ─────────────────────────────────────
class ConfirmSkillsRequest(BaseModel):
    skills: List[str] = Field(
        ...,
        description="Canonical skills to add to your profile. Each must have been "
                    "passed in this attempt.",
    )


class ConfirmSkillsResponse(BaseModel):
    added: List[str] = []
    already_present: List[str] = []
    skills: List[dict] = []
    message: str = ""
