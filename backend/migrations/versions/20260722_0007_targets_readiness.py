"""add targets criteria mappings and readiness assessments

Revision ID: 20260722_0007
Revises: 20260721_0006
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260722_0007"
down_revision: str | None = "20260721_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "targets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("target_type", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("provenance", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    for name, column in [
        ("ix_targets_title", "title"),
        ("ix_targets_target_type", "target_type"),
        ("ix_targets_status", "status"),
    ]:
        op.create_index(name, "targets", [column])
    op.create_table(
        "target_criteria",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("provenance", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["target_id"], ["targets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_target_criteria_target_id", "target_criteria", ["target_id"])
    op.create_table(
        "criterion_asset_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("criterion_id", sa.Uuid(), nullable=False),
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["criterion_id"], ["target_criteria.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["asset_id"], ["career_assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("criterion_id", "asset_id"),
    )
    op.create_index("ix_criterion_asset_links_criterion_id", "criterion_asset_links", ["criterion_id"])
    op.create_index("ix_criterion_asset_links_asset_id", "criterion_asset_links", ["asset_id"])
    op.create_table(
        "criterion_evidence_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("criterion_id", sa.Uuid(), nullable=False),
        sa.Column("evidence_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["criterion_id"], ["target_criteria.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["evidence_id"], ["evidence_items.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("criterion_id", "evidence_id"),
    )
    op.create_index("ix_criterion_evidence_links_criterion_id", "criterion_evidence_links", ["criterion_id"])
    op.create_index("ix_criterion_evidence_links_evidence_id", "criterion_evidence_links", ["evidence_id"])
    op.create_table(
        "readiness_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("algorithm_version", sa.String(50), nullable=False),
        sa.Column("readiness_score", sa.Float(), nullable=False),
        sa.Column("overall_confidence", sa.Float(), nullable=False),
        sa.Column("strengths_json", sa.Text(), nullable=False),
        sa.Column("gaps_json", sa.Text(), nullable=False),
        sa.Column("recommendations_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["target_id"], ["targets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_readiness_assessments_target_id", "readiness_assessments", ["target_id"])
    op.create_index("ix_readiness_assessments_created_at", "readiness_assessments", ["created_at"])
    op.create_table(
        "criterion_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("readiness_assessment_id", sa.Uuid(), nullable=False),
        sa.Column("criterion_id", sa.Uuid(), nullable=False),
        sa.Column("criterion_title", sa.String(300), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("normalized_weight", sa.Float(), nullable=False),
        sa.Column("coverage", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("asset_ids_json", sa.Text(), nullable=False),
        sa.Column("evidence_ids_json", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["readiness_assessment_id"], ["readiness_assessments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["criterion_id"], ["target_criteria.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_criterion_assessments_readiness_assessment_id", "criterion_assessments", ["readiness_assessment_id"])
    op.create_index("ix_criterion_assessments_criterion_id", "criterion_assessments", ["criterion_id"])


def downgrade() -> None:
    op.drop_table("criterion_assessments")
    op.drop_table("readiness_assessments")
    op.drop_table("criterion_evidence_links")
    op.drop_table("criterion_asset_links")
    op.drop_table("target_criteria")
    op.drop_table("targets")
