"""Add fellowship tracking.

Revision ID: 20260730_0012
Revises: 20260728_0011
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260730_0012"
down_revision: str | None = "20260728_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fellowships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("organisation", sa.String(250), nullable=False),
        sa.Column("website", sa.String(1000), nullable=False),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=True),
        sa.Column("opportunity_id", sa.Uuid(), nullable=True),
        sa.Column("sponsor_name", sa.String(250), nullable=False),
        sa.Column("sponsor_status", sa.String(30), nullable=False),
        sa.Column("next_action", sa.String(500), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.ForeignKeyConstraint(["target_id"], ["targets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fellowships_name", "fellowships", ["name"])
    op.create_index("ix_fellowships_deadline", "fellowships", ["deadline"])
    op.create_index("ix_fellowships_status", "fellowships", ["status"])
    op.create_index("ix_fellowships_updated_at", "fellowships", ["updated_at"])


def downgrade() -> None:
    op.drop_table("fellowships")
