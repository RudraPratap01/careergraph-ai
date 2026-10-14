"""
Profile models — StudentProfile and AlumniProfile.

Phase 2: User Profiles
Links directly to the 'users' table via foreign key (user_id).
Preserves existing User model and relational structure.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.database.session import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    # Academic background
    college = Column(String(255), nullable=True)
    degree = Column(String(255), nullable=True)  # e.g., B.Tech Computer Science & Engineering
    current_year = Column(Integer, nullable=True)  # 1, 2, 3, 4
    graduation_year = Column(Integer, nullable=True)  # e.g., 2026
    cgpa = Column(Float, nullable=True)

    # Career orientation
    target_role = Column(String(255), nullable=True)  # e.g., Backend Developer, ML Engineer
    target_timeline_months = Column(Integer, nullable=True, default=6)  # e.g., 3, 6, 12 months

    # Bio and external links
    bio = Column(Text, nullable=True)
    github_username = Column(String(255), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    portfolio_url = Column(String(500), nullable=True)

    # Self-reported skills: [{"name": "Python", "level": "intermediate"}, ...]
    skills = Column(JSON, nullable=True, default=list)

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

    # Relationship back to User
    user = relationship("User", back_populates="student_profile")

    def __repr__(self) -> str:
        return f"<StudentProfile id={self.id} user_id={self.user_id} target_role={self.target_role}>"


class AlumniProfile(Base):
    __tablename__ = "alumni_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    # Professional background
    company = Column(String(255), nullable=True)
    job_title = Column(String(255), nullable=True)  # e.g., Senior Software Engineer
    years_of_experience = Column(Integer, nullable=True, default=0)

    # Alma mater
    college = Column(String(255), nullable=True)
    graduation_year = Column(Integer, nullable=True)

    # Mentorship configuration
    expertise_areas = Column(JSON, nullable=True, default=list)  # e.g., ["System Design", "Python", "FastAPI"]
    bio = Column(Text, nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    github_username = Column(String(255), nullable=True)
    meeting_link = Column(String(500), nullable=True)

    is_available_for_mentoring = Column(Boolean, default=True, nullable=False)
    max_mentees = Column(Integer, default=3, nullable=False)

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

    # Relationship back to User
    user = relationship("User", back_populates="alumni_profile")

    def __repr__(self) -> str:
        return f"<AlumniProfile id={self.id} user_id={self.user_id} company={self.company}>"
