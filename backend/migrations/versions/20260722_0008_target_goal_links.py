"""map career targets to strategic goals

Revision ID: 20260722_0008
Revises: 20260722_0007
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260722_0008"
down_revision: str | None = "20260722_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "target_goal_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("goal_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["target_id"], ["targets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["goal_id"], ["strategic_goals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("target_id", "goal_id"),
    )
    op.create_index("ix_target_goal_links_target_id", "target_goal_links", ["target_id"])
    op.create_index("ix_target_goal_links_goal_id", "target_goal_links", ["goal_id"])


def downgrade() -> None:
    op.drop_table("target_goal_links")
