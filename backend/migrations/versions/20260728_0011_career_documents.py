"""Add reusable career documents.

Revision ID: 20260728_0011
Revises: 20260722_0010
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260728_0011"
down_revision: str | None = "20260722_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "career_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("audience", sa.String(300), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("tone", sa.String(50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("asset_ids_json", sa.Text(), nullable=False),
        sa.Column("unsupported_claims_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_career_documents_document_type", "career_documents", ["document_type"])
    op.create_index("ix_career_documents_title", "career_documents", ["title"])
    op.create_index("ix_career_documents_created_at", "career_documents", ["created_at"])


def downgrade() -> None:
    op.drop_table("career_documents")
