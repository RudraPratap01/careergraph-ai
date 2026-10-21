"""
GitHub verification model — Phase 6.

One row per student: the last successful verification of their public GitHub
account. The row is the source of truth for "is this account linked?", because
``StudentProfile.github_username`` is a plain editable field that a normal
profile save can overwrite.

Only public data returned by GitHub's REST API is stored. No OAuth tokens, no
private repository contents and no commit-level data are persisted.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)

from app.database.session import Base


class GitHubVerification(Base):
    __tablename__ = "github_verifications"

    id = Column(Integer, primary_key=True, index=True)

    # One linked GitHub account per user.
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )

    # A GitHub login may only be claimed by one account, so a second student
    # cannot present someone else's repositories as their own evidence.
    username = Column(String(100), unique=True, nullable=False, index=True)

    # Public profile snapshot (as returned by GitHub at fetch time).
    name = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    profile_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    public_repos = Column(Integer, nullable=False, default=0)
    followers = Column(Integer, nullable=False, default=0)
    following = Column(Integer, nullable=False, default=0)
    account_created_at = Column(DateTime(timezone=True), nullable=True)

    # Repository analysis summary.
    repos_analyzed = Column(Integer, nullable=False, default=0)
    repos_truncated = Column(Boolean, nullable=False, default=False)
    forks_excluded = Column(Integer, nullable=False, default=0)
    total_stars = Column(Integer, nullable=False, default=0)

    # [{"name": "Python", "count": 4}, ...]
    languages = Column(JSON, nullable=True, default=list)
    # [{"name": "Python", "category": "Languages", "confidence": 0.88, ...}, ...]
    detected_skills = Column(JSON, nullable=True, default=list)

    fetched_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
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

    def __repr__(self) -> str:
        return f"<GitHubVerification id={self.id} user_id={self.user_id} username={self.username}>"
