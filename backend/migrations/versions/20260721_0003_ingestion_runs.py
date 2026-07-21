"""add reviewed career ingestion runs

Revision ID: 20260721_0003
Revises: f3396633e04e
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "20260721_0003"
down_revision: str | None = "f3396633e04e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source_type", sqlmodel.sql.sqltypes.AutoString(length=30), nullable=False),
        sa.Column("source_label", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column("source_url", sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=True),
        sa.Column(
            "ai_handling_policy", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False
        ),
        sa.Column("provider", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(length=30), nullable=False),
        sa.Column("proposal_json", sa.Text(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("applied_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ingestion_runs_source_type"), "ingestion_runs", ["source_type"])
    op.create_index(op.f("ix_ingestion_runs_status"), "ingestion_runs", ["status"])
    op.create_index(op.f("ix_ingestion_runs_created_at"), "ingestion_runs", ["created_at"])


def downgrade() -> None:
    op.drop_index(op.f("ix_ingestion_runs_created_at"), table_name="ingestion_runs")
    op.drop_index(op.f("ix_ingestion_runs_status"), table_name="ingestion_runs")
    op.drop_index(op.f("ix_ingestion_runs_source_type"), table_name="ingestion_runs")
    op.drop_table("ingestion_runs")
