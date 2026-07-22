"""add evidence-grounded strategic goal assessments

Revision ID: 20260722_0009
Revises: 20260722_0008
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260722_0009"
down_revision: str | None = "20260722_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "strategic_goal_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("goal_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("readiness_score", sa.Float(), nullable=False),
        sa.Column("overall_confidence", sa.Float(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("strengths_json", sa.Text(), nullable=False),
        sa.Column("gaps_json", sa.Text(), nullable=False),
        sa.Column("recommendations_json", sa.Text(), nullable=False),
        sa.Column("asset_ids_json", sa.Text(), nullable=False),
        sa.Column("evidence_ids_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["goal_id"], ["strategic_goals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_strategic_goal_assessments_goal_id", "strategic_goal_assessments", ["goal_id"])
    op.create_index("ix_strategic_goal_assessments_created_at", "strategic_goal_assessments", ["created_at"])


def downgrade() -> None:
    op.drop_table("strategic_goal_assessments")
