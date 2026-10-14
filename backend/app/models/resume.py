"""
Resume model — stored in the 'resumes' table.

Phase 3: Resume Intelligence
Stores uploaded resume metadata, raw extracted text, and parsed skills with confidence & evidence.
Links to User via user_id foreign key.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database.session import Base


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # "pdf", "docx", "txt"
    file_size_bytes = Column(Integer, nullable=False)
    raw_text = Column(Text, nullable=True)

    # Extracted skills with confidence and evidence:
    # [{"name": "FastAPI", "normalized_name": "FastAPI", "category": "Frameworks", "confidence": 0.95, "evidence": "..."}, ...]
    extracted_skills = Column(JSON, nullable=True, default=list)

    # Status: "parsed" (waiting student review), "reviewed" (confirmed by student)
    status = Column(String(50), default="parsed", nullable=False)

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

    user = relationship("User", back_populates="resumes")

    def __repr__(self) -> str:
        return f"<Resume id={self.id} user_id={self.user_id} filename='{self.filename}' status='{self.status}'>"
