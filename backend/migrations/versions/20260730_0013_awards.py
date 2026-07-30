"""Add awards and recognition tracking.

Revision ID: 20260730_0013
Revises: 20260730_0012
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260730_0013"
down_revision: str | None = "20260730_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "award_pathways",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(300), nullable=False),
        sa.Column("organisation", sa.String(250), nullable=False),
        sa.Column("award_type", sa.String(60), nullable=False),
        sa.Column("website", sa.String(1000), nullable=False),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=True),
        sa.Column("opportunity_id", sa.Uuid(), nullable=True),
        sa.Column("nominator_name", sa.String(250), nullable=False),
        sa.Column("nominator_status", sa.String(30), nullable=False),
        sa.Column("dossier_status", sa.String(30), nullable=False),
        sa.Column("next_action", sa.String(500), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"]),
        sa.ForeignKeyConstraint(["target_id"], ["targets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_award_pathways_name", "award_pathways", ["name"])
    op.create_index("ix_award_pathways_award_type", "award_pathways", ["award_type"])
    op.create_index("ix_award_pathways_deadline", "award_pathways", ["deadline"])
    op.create_index("ix_award_pathways_status", "award_pathways", ["status"])
    op.create_index("ix_award_pathways_updated_at", "award_pathways", ["updated_at"])


def downgrade() -> None:
    op.drop_table("award_pathways")
