from datetime import UTC, date, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import Column, Text, UniqueConstraint
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


class Provenance(StrEnum):
    USER = "user"
    IMPORT = "import"
    EXTRACTED = "extracted"
    AI = "ai"
    RULE = "rule"


class AssetStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class Visibility(StrEnum):
    PUBLIC = "public"
    PROFESSIONAL = "professional"


class AiHandlingPolicy(StrEnum):
    AI_ALLOWED = "ai_allowed"
    LOCAL_ONLY = "local_only"
    REDACTED = "redacted"


class GoalHorizon(StrEnum):
    SHORT = "short_term"
    MEDIUM = "medium_term"
    LONG = "long_term"


class AssetThemeLink(SQLModel, table=True):
    __tablename__ = "asset_theme_links"
    __table_args__ = (UniqueConstraint("asset_id", "theme_id"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    asset_id: UUID = Field(foreign_key="career_assets.id", index=True, ondelete="CASCADE")
    theme_id: UUID = Field(foreign_key="themes.id", index=True, ondelete="CASCADE")
    provenance: str = Field(default=Provenance.USER.value, max_length=20)
    created_at: datetime = Field(default_factory=utc_now)


class CareerProfile(SQLModel, table=True):
    __tablename__ = "career_profiles"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(default="", max_length=200)
    current_title: str = Field(default="", max_length=250)
    current_organisation: str = Field(default="", max_length=250)
    career_mission: str = Field(default="", sa_column=Column(Text, nullable=False))
    career_narrative: str = Field(default="", sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Theme(SQLModel, table=True):
    __tablename__ = "themes"
    __table_args__ = (UniqueConstraint("name"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=100, index=True)
    description: str = Field(default="", sa_column=Column(Text, nullable=False))
    provenance: str = Field(default=Provenance.USER.value, max_length=20)
    created_at: datetime = Field(default_factory=utc_now)


class StrategicGoal(SQLModel, table=True):
    __tablename__ = "strategic_goals"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str = Field(max_length=200)
    description: str = Field(default="", sa_column=Column(Text, nullable=False))
    horizon: str = Field(default=GoalHorizon.MEDIUM.value, max_length=20, index=True)
    status: str = Field(default="active", max_length=20, index=True)
    target_date: date | None = None
    provenance: str = Field(default=Provenance.USER.value, max_length=20)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Organisation(SQLModel, table=True):
    __tablename__ = "organisations"
    __table_args__ = (UniqueConstraint("name"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=250, index=True)
    organisation_type: str = Field(default="", max_length=100)
    website: str = Field(default="", max_length=500)
    notes: str = Field(default="", sa_column=Column(Text, nullable=False))
    provenance: str = Field(default=Provenance.USER.value, max_length=20)
    created_at: datetime = Field(default_factory=utc_now)


class Person(SQLModel, table=True):
    __tablename__ = "people"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(max_length=200, index=True)
    title: str = Field(default="", max_length=250)
    organisation_id: UUID | None = Field(default=None, foreign_key="organisations.id")
    relationship_type: str = Field(default="professional_contact", max_length=100)
    public_profile_url: str = Field(default="", max_length=500)
    notes: str = Field(default="", sa_column=Column(Text, nullable=False))
    provenance: str = Field(default=Provenance.USER.value, max_length=20)
    created_at: datetime = Field(default_factory=utc_now)


class CareerAsset(SQLModel, table=True):
    __tablename__ = "career_assets"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str = Field(max_length=300, index=True)
    description: str = Field(default="", sa_column=Column(Text, nullable=False))
    category: str = Field(max_length=100, index=True)
    subcategory: str = Field(default="", max_length=100)
    start_date: date | None = Field(default=None, index=True)
    end_date: date | None = None
    date_precision: str = Field(default="day", max_length=20)
    status: str = Field(default=AssetStatus.ACTIVE.value, max_length=20, index=True)
    impact_summary: str = Field(default="", sa_column=Column(Text, nullable=False))
    organisation_id: UUID | None = Field(default=None, foreign_key="organisations.id")
    role: str = Field(default="", max_length=250)
    visibility: str = Field(default=Visibility.PUBLIC.value, max_length=20)
    tags_json: str = Field(default="[]", sa_column=Column(Text, nullable=False))
    keywords_json: str = Field(default="[]", sa_column=Column(Text, nullable=False))
    source_kind: str = Field(default=Provenance.USER.value, max_length=20)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    archived_at: datetime | None = None


class Document(SQLModel, table=True):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("sha256"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    original_filename: str = Field(max_length=255)
    mime_type: str = Field(max_length=150)
    byte_size: int
    sha256: str = Field(max_length=64, index=True)
    relative_path: str = Field(max_length=500)
    ai_handling_policy: str = Field(default=AiHandlingPolicy.LOCAL_ONLY.value, max_length=20)
    extracted_text: str = Field(default="", sa_column=Column(Text, nullable=False))
    extraction_status: str = Field(default="pending", max_length=30)
    extraction_error: str = Field(default="", sa_column=Column(Text, nullable=False))
    source_kind: str = Field(default=Provenance.USER.value, max_length=20)
    created_at: datetime = Field(default_factory=utc_now)


class EvidenceItem(SQLModel, table=True):
    __tablename__ = "evidence_items"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    asset_id: UUID = Field(foreign_key="career_assets.id", index=True, ondelete="CASCADE")
    document_id: UUID | None = Field(default=None, foreign_key="documents.id")
    title: str = Field(max_length=250)
    description: str = Field(default="", sa_column=Column(Text, nullable=False))
    source_url: str = Field(default="", max_length=1000)
    source_kind: str = Field(default=Provenance.USER.value, max_length=20)
    created_at: datetime = Field(default_factory=utc_now)


class AuditEvent(SQLModel, table=True):
    __tablename__ = "audit_events"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    entity_type: str = Field(max_length=100, index=True)
    entity_id: str = Field(max_length=100, index=True)
    action: str = Field(max_length=100, index=True)
    actor: str = Field(default="local_user", max_length=50)
    source: str = Field(default=Provenance.USER.value, max_length=20)
    details_json: str = Field(default="{}", sa_column=Column(Text, nullable=False))
    occurred_at: datetime = Field(default_factory=utc_now, index=True)


class IngestionRun(SQLModel, table=True):
    __tablename__ = "ingestion_runs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    source_type: str = Field(max_length=30, index=True)
    source_label: str = Field(max_length=500)
    source_url: str = Field(default="", max_length=1_000)
    document_id: UUID | None = Field(default=None, foreign_key="documents.id")
    ai_handling_policy: str = Field(default=AiHandlingPolicy.LOCAL_ONLY.value, max_length=20)
    provider: str = Field(default="deterministic", max_length=50)
    status: str = Field(default="ready_for_review", max_length=30, index=True)
    proposal_json: str = Field(default="{}", sa_column=Column(Text, nullable=False))
    error_message: str = Field(default="", sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(default_factory=utc_now, index=True)
    applied_at: datetime | None = None
