"""phase 8 assessment & mentorship tables

Revision ID: 0003_assessments_mentorship
Revises: 0002_roadmaps
Create Date: 2026-10-18

Adds Phase 8 persistence: skill-assessment attempts and mentorship requests.
Additive only — no existing tables are modified or dropped.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_assessments_mentorship"
down_revision: Union[str, None] = "0002_roadmaps"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "assessment_attempts",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("assessment_key", sa.String(length=100), nullable=False),
        sa.Column("assessment_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="in_progress"),
        sa.Column("score_percent", sa.Integer(), nullable=True),
        sa.Column("passed", sa.Boolean(), nullable=True),
        sa.Column("correct_count", sa.Integer(), nullable=True),
        sa.Column("total_count", sa.Integer(), nullable=True),
        sa.Column("results", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_assessment_attempts_user_id", "assessment_attempts", ["user_id"], unique=False)
    op.create_index("ix_assessment_attempts_id", "assessment_attempts", ["id"], unique=False)

    op.create_table(
        "mentorship_requests",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("alumni_id", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("match_score", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["alumni_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_mentorship_requests_student_id", "mentorship_requests", ["student_id"], unique=False)
    op.create_index("ix_mentorship_requests_alumni_id", "mentorship_requests", ["alumni_id"], unique=False)
    op.create_index("ix_mentorship_requests_status", "mentorship_requests", ["status"], unique=False)
    op.create_index("ix_mentorship_requests_id", "mentorship_requests", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_mentorship_requests_id", table_name="mentorship_requests")
    op.drop_index("ix_mentorship_requests_status", table_name="mentorship_requests")
    op.drop_index("ix_mentorship_requests_alumni_id", table_name="mentorship_requests")
    op.drop_index("ix_mentorship_requests_student_id", table_name="mentorship_requests")
    op.drop_table("mentorship_requests")

    op.drop_index("ix_assessment_attempts_id", table_name="assessment_attempts")
    op.drop_index("ix_assessment_attempts_user_id", table_name="assessment_attempts")
    op.drop_table("assessment_attempts")
