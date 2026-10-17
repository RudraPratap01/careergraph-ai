"""
Roadmap models — Phase 5: Skill dependency graph & learning roadmap.

Stores a generated learning roadmap (one active roadmap per user/occupation) and
per-step progress. Steps themselves are snapshotted as JSON so the roadmap is
stable even if the catalog changes; progress lives in its own table so a single
step can be updated without rewriting the snapshot.
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
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database.session import Base


class Roadmap(Base):
    __tablename__ = "roadmaps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    occupation_key = Column(String(100), nullable=False)
    occupation_name = Column(String(255), nullable=False)
    occupation_category = Column(String(100), nullable=True)

    # Where the occupation came from: "request" or "profile.target_role"
    target_source = Column(String(50), default="request", nullable=False)

    # Which graph backend produced the dependency information ("memory" | "neo4j")
    graph_backend = Column(String(50), default="memory", nullable=False)

    # True when dependency data was incomplete and the roadmap is partial
    is_partial = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)

    # Ordered step snapshot: [{"skill", "position", "depth", "reason", ...}]
    steps = Column(JSON, nullable=False, default=list)

    # Required skills the user already possesses (reported, never re-taught)
    possessed_skills = Column(JSON, nullable=False, default=list)

    status = Column(String(50), default="active", nullable=False)

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

    user = relationship("User", back_populates="roadmaps")
    step_progress = relationship(
        "RoadmapStepProgress",
        back_populates="roadmap",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Roadmap id={self.id} user_id={self.user_id} occupation={self.occupation_key}>"


class RoadmapStepProgress(Base):
    __tablename__ = "roadmap_step_progress"
    __table_args__ = (
        UniqueConstraint("roadmap_id", "skill", name="uq_roadmap_step_skill"),
    )

    id = Column(Integer, primary_key=True, index=True)
    roadmap_id = Column(Integer, ForeignKey("roadmaps.id", ondelete="CASCADE"), nullable=False, index=True)

    skill = Column(String(100), nullable=False)
    position = Column(Integer, nullable=False, default=0)

    # pending | in_progress | completed
    state = Column(String(20), default="pending", nullable=False)

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    roadmap = relationship("Roadmap", back_populates="step_progress")

    def __repr__(self) -> str:
        return f"<RoadmapStepProgress roadmap_id={self.roadmap_id} skill={self.skill} state={self.state}>"
