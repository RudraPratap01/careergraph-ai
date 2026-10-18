"""
Assessment models — Phase 8: assessments.

An attempt is created when a student starts an assessment and is graded on
submit. Results (per-question and per-skill) are snapshotted as JSON so the
attempt stays meaningful even if the curated bank is later edited.

The correct answers are never stored on the attempt response; grading happens
server-side in ``app/services/assessment_service.py``.
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from app.database.session import Base

STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"


class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    assessment_key = Column(String(100), nullable=False)
    assessment_name = Column(String(255), nullable=False)

    # in_progress | completed
    status = Column(String(20), default=STATUS_IN_PROGRESS, nullable=False)

    # Populated on submit
    score_percent = Column(Integer, nullable=True)
    passed = Column(Boolean, nullable=True)

    correct_count = Column(Integer, nullable=True)
    total_count = Column(Integer, nullable=True)

    # Snapshot: {"answers": [...], "skills": [...], "passed_skills": [...]}
    results = Column(JSON, nullable=True)

    started_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="assessment_attempts")

    def __repr__(self) -> str:
        return (
            f"<AssessmentAttempt id={self.id} user_id={self.user_id} "
            f"key={self.assessment_key} status={self.status}>"
        )
