"""phase 5 roadmap tables

Revision ID: 0002_roadmaps
Revises: 0001_baseline
Create Date: 2026-10-17

Adds Phase 5 persistence: generated roadmaps and per-step progress.
Additive only — no existing tables are modified or dropped.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_roadmaps"
down_revision: Union[str, None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "roadmaps",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("occupation_key", sa.String(length=100), nullable=False),
        sa.Column("occupation_name", sa.String(length=255), nullable=False),
        sa.Column("occupation_category", sa.String(length=100), nullable=True),
        sa.Column("target_source", sa.String(length=50), nullable=False, server_default="request"),
        sa.Column("graph_backend", sa.String(length=50), nullable=False, server_default="memory"),
        sa.Column("is_partial", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("steps", sa.JSON(), nullable=False),
        sa.Column("possessed_skills", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_roadmaps_user_id", "roadmaps", ["user_id"], unique=False)
    op.create_index("ix_roadmaps_id", "roadmaps", ["id"], unique=False)

    op.create_table(
        "roadmap_step_progress",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("roadmap_id", sa.Integer(), nullable=False),
        sa.Column("skill", sa.String(length=100), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("state", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["roadmap_id"], ["roadmaps.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("roadmap_id", "skill", name="uq_roadmap_step_skill"),
    )
    op.create_index("ix_roadmap_step_progress_roadmap_id", "roadmap_step_progress", ["roadmap_id"], unique=False)
    op.create_index("ix_roadmap_step_progress_id", "roadmap_step_progress", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_roadmap_step_progress_id", table_name="roadmap_step_progress")
    op.drop_index("ix_roadmap_step_progress_roadmap_id", table_name="roadmap_step_progress")
    op.drop_table("roadmap_step_progress")
    op.drop_index("ix_roadmaps_id", table_name="roadmaps")
    op.drop_index("ix_roadmaps_user_id", table_name="roadmaps")
    op.drop_table("roadmaps")
