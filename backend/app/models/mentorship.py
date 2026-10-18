"""
Mentorship models — Phase 8: alumni matching.

A mentorship request is created by a student for a specific alumni mentor. The
alumni can accept or decline it; the requesting student can cancel it.

The match score is snapshotted at request time so the request keeps the
rationale it was made on, even if profiles change afterwards.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.session import Base

STATUS_PENDING = "pending"
STATUS_ACCEPTED = "accepted"
STATUS_DECLINED = "declined"
STATUS_CANCELLED = "cancelled"

OPEN_STATUSES = (STATUS_PENDING,)
CLOSED_STATUSES = (STATUS_DECLINED, STATUS_CANCELLED)


class MentorshipRequest(Base):
    __tablename__ = "mentorship_requests"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    alumni_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    message = Column(Text, nullable=True)

    # pending | accepted | declined | cancelled
    status = Column(String(20), default=STATUS_PENDING, nullable=False, index=True)

    # Deterministic match score at the time of the request (0-100)
    match_score = Column(Integer, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    student = relationship("User", foreign_keys=[student_id], back_populates="sent_mentorship_requests")
    alumni = relationship("User", foreign_keys=[alumni_id], back_populates="received_mentorship_requests")

    def __repr__(self) -> str:
        return (
            f"<MentorshipRequest id={self.id} student_id={self.student_id} "
            f"alumni_id={self.alumni_id} status={self.status}>"
        )
