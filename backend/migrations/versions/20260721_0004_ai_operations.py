"""add AI operation telemetry

Revision ID: 20260721_0004
Revises: 20260721_0003
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "20260721_0004"
down_revision: str | None = "20260721_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_operations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("operation", sqlmodel.sql.sqltypes.AutoString(length=80), nullable=False),
        sa.Column("entity_type", sqlmodel.sql.sqltypes.AutoString(length=80), nullable=False),
        sa.Column("entity_id", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("provider", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column("model", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(length=30), nullable=False),
        sa.Column("input_characters", sa.Integer(), nullable=False),
        sa.Column("output_characters", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("operation", "entity_type", "entity_id", "status", "created_at"):
        op.create_index(op.f(f"ix_ai_operations_{column}"), "ai_operations", [column])


def downgrade() -> None:
    for column in reversed(("operation", "entity_type", "entity_id", "status", "created_at")):
        op.drop_index(op.f(f"ix_ai_operations_{column}"), table_name="ai_operations")
    op.drop_table("ai_operations")
