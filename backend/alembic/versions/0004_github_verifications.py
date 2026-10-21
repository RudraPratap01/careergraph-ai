"""phase 6 github verification table

Revision ID: 0004_github_verifications
Revises: 0003_assessments_mentorship
Create Date: 2026-10-21

Adds Phase 6 persistence: the last successful public GitHub verification for a
student. Additive only - no existing tables are modified or dropped.

``student_profiles.github_username`` already exists (Phase 2) and is used as a
display mirror only; this table is the source of truth for whether an account is
currently linked.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004_github_verifications"
down_revision: Union[str, None] = "0003_assessments_mentorship"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "github_verifications",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("profile_url", sa.String(length=500), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("public_repos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("followers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("following", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("account_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("repos_analyzed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("repos_truncated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("forks_excluded", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_stars", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("languages", sa.JSON(), nullable=True),
        sa.Column("detected_skills", sa.JSON(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_github_verifications_id", "github_verifications", ["id"], unique=False
    )
    op.create_index(
        "ix_github_verifications_user_id",
        "github_verifications",
        ["user_id"],
        unique=True,
    )
    op.create_index(
        "ix_github_verifications_username",
        "github_verifications",
        ["username"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_github_verifications_username", table_name="github_verifications")
    op.drop_index("ix_github_verifications_user_id", table_name="github_verifications")
    op.drop_index("ix_github_verifications_id", table_name="github_verifications")
    op.drop_table("github_verifications")
