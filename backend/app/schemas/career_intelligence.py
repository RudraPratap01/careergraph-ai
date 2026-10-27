"""
Phase 7 schemas - grounded career-intelligence requests and responses.

The deterministic readiness and roadmap values are returned separately from any
LLM explanation. An LLM can explain them, but it cannot replace or recompute
them. Source citations always refer to the retrieved curated chunks in the same
response.
"""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class AdvisorRequest(BaseModel):
    """A question about the authenticated student's career-learning path."""

    question: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Career-learning question, grounded in the user's gap and roadmap.",
    )
    occupation: Optional[str] = Field(
        None,
        max_length=120,
        description=(
            "Optional occupation key/name. Defaults to the student's saved target role. "
            "An unknown occupation is rejected rather than silently ignored."
        ),
    )

    @field_validator("question")
    @classmethod
    def _strip_question(cls, value: str) -> str:
        stripped = value.strip()
        if len(stripped) < 3:
            raise ValueError("question must contain at least 3 non-whitespace characters")
        return stripped

    @field_validator("occupation")
    @classmethod
    def _strip_occupation(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class KnowledgeSource(BaseModel):
    """A retrieved curated chunk, cited by its stable ``S1``-style ID."""

    id: str = Field(..., pattern=r"^S\d+$")
    document_id: str
    title: str
    source: str
    source_label: str
    kind: str
    score: float = Field(..., ge=0)
    snippet: str


class AdvisorContext(BaseModel):
    """Deterministic context shown alongside the explanation."""

    occupation_key: Optional[str] = None
    occupation_name: Optional[str] = None
    readiness_score: Optional[int] = Field(None, ge=0, le=100)
    readiness_band: Optional[str] = None
    matched_count: Optional[int] = None
    required_count: Optional[int] = None
    known_skills: List[str] = []
    missing_skills: List[str] = []
    roadmap_steps: List[str] = []
    graph_backend: str = "memory"


class AdvisorResponse(BaseModel):
    """Answer plus the evidence and deterministic context used to produce it."""

    answer: str
    mode: Literal["llm", "grounded_extractive"]
    retrieval: str = "lexical_bm25"
    llm_configured: bool
    llm_used: bool
    provider: str = "openrouter"
    model: Optional[str] = None
    sources: List[KnowledgeSource] = []
    context: AdvisorContext
    notice: Optional[str] = None
    limitations: List[str] = []
    privacy_note: str
    disclaimer: str
    request_id: str


class AdvisorStatus(BaseModel):
    """Configuration and corpus status. Never exposes credentials."""

    enabled: bool = True
    retrieval: str = "lexical_bm25"
    llm_configured: bool
    provider: str = "openrouter"
    model: Optional[str] = None
    knowledge: Dict[str, Any]
    limitations: List[str] = []
    privacy_note: str
    disclaimer: str
