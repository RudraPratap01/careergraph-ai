"""
User model — stored in the 'users' table.

This is the single source of truth for identity in CareerGraph AI.
Separate profile tables (StudentProfile, AlumniProfile) will link here
via foreign keys in Phase 2.

Roles:
  student  — can analyze their skills and request mentorship
  alumni   — can mentor students
  admin    — manages the platform
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
import enum

from app.database.session import Base


class UserRole(str, enum.Enum):
    STUDENT = "student"
    ALUMNI = "alumni"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)

    # Passwords are stored as bcrypt hashes — never plaintext
    hashed_password = Column(String(255), nullable=False)

    role = Column(Enum(UserRole), nullable=False, default=UserRole.STUDENT)

    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

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

    # Profile relationships (Phase 2)
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    alumni_profile = relationship("AlumniProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

    # Resume relationships (Phase 3)
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"
