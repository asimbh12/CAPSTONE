"""add opportunities and versioned assessments

Revision ID: 20260721_0006
Revises: 20260721_0005
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "20260721_0006"
down_revision: str | None = "20260721_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    op.create_table("opportunities", sa.Column("id", sa.Uuid(), nullable=False), sa.Column("title", sa.String(300), nullable=False), sa.Column("description", sa.Text(), nullable=False), sa.Column("opportunity_type", sa.String(100), nullable=False), sa.Column("organisation_id", sa.Uuid(), nullable=True), sa.Column("url", sa.String(1000), nullable=False), sa.Column("opening_date", sa.Date(), nullable=True), sa.Column("closing_date", sa.Date(), nullable=True), sa.Column("status", sa.String(20), nullable=False), sa.Column("owner", sa.String(200), nullable=False), sa.Column("next_action", sa.String(500), nullable=False), sa.Column("notes", sa.Text(), nullable=False), sa.Column("source", sa.String(50), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False), sa.Column("updated_at", sa.DateTime(), nullable=False), sa.Column("archived_at", sa.DateTime(), nullable=True), sa.ForeignKeyConstraint(["organisation_id"], ["organisations.id"]), sa.PrimaryKeyConstraint("id"))
    for name, column in [("ix_opportunities_title", "title"), ("ix_opportunities_opportunity_type", "opportunity_type"), ("ix_opportunities_closing_date", "closing_date"), ("ix_opportunities_status", "status")]: op.create_index(name, "opportunities", [column])
    op.create_table("opportunity_assessments", sa.Column("id", sa.Uuid(), nullable=False), sa.Column("opportunity_id", sa.Uuid(), nullable=False), sa.Column("algorithm_version", sa.String(50), nullable=False), sa.Column("strategic_value", sa.Integer(), nullable=False), sa.Column("probability", sa.Integer(), nullable=False), sa.Column("effort", sa.Integer(), nullable=False), sa.Column("raw_score", sa.Float(), nullable=False), sa.Column("normalized_score", sa.Float(), nullable=False), sa.Column("input_source", sa.String(20), nullable=False), sa.Column("explanation", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False), sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_opportunity_assessments_opportunity_id", "opportunity_assessments", ["opportunity_id"]); op.create_index("ix_opportunity_assessments_created_at", "opportunity_assessments", ["created_at"])

def downgrade() -> None:
    op.drop_table("opportunity_assessments"); op.drop_table("opportunities")
