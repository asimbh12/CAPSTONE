from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.career import AiHandlingPolicy, AssetStatus, GoalHorizon, Visibility


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProfileInput(ApiModel):
    name: str = Field(default="", max_length=200)
    current_title: str = Field(default="", max_length=250)
    current_organisation: str = Field(default="", max_length=250)
    career_mission: str = Field(default="", max_length=10_000)
    career_narrative: str = Field(default="", max_length=30_000)


class ProfileRead(ProfileInput):
    id: UUID
    created_at: datetime
    updated_at: datetime


class ThemeCreate(ApiModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=5_000)


class ThemeRead(ThemeCreate):
    id: UUID
    provenance: str
    created_at: datetime


class GoalCreate(ApiModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=10_000)
    horizon: GoalHorizon = GoalHorizon.MEDIUM
    target_date: date | None = None


class GoalRead(GoalCreate):
    id: UUID
    status: str
    provenance: str
    created_at: datetime
    updated_at: datetime


class GoalAchievementCreate(ApiModel):
    achieved_date: date = Field(default_factory=date.today)
    impact_summary: str = Field(default="", max_length=30_000)


class OrganisationCreate(ApiModel):
    name: str = Field(min_length=1, max_length=250)
    organisation_type: str = Field(default="", max_length=100)
    website: str = Field(default="", max_length=500)
    notes: str = Field(default="", max_length=10_000)


class OrganisationRead(OrganisationCreate):
    id: UUID
    provenance: str
    created_at: datetime


class PersonCreate(ApiModel):
    name: str = Field(min_length=1, max_length=200)
    title: str = Field(default="", max_length=250)
    organisation_id: UUID | None = None
    relationship_type: str = Field(default="professional_contact", max_length=100)
    public_profile_url: str = Field(default="", max_length=500)
    notes: str = Field(default="", max_length=10_000)


class PersonRead(PersonCreate):
    id: UUID
    provenance: str
    created_at: datetime


class AssetCreate(ApiModel):
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(default="", max_length=30_000)
    category: str = Field(min_length=1, max_length=100)
    subcategory: str = Field(default="", max_length=100)
    start_date: date | None = None
    end_date: date | None = None
    date_precision: str = Field(default="day", max_length=20)
    status: AssetStatus = AssetStatus.ACTIVE
    impact_summary: str = Field(default="", max_length=30_000)
    organisation_id: UUID | None = None
    role: str = Field(default="", max_length=250)
    visibility: Visibility = Visibility.PUBLIC
    tags: list[str] = Field(default_factory=list, max_length=50)
    keywords: list[str] = Field(default_factory=list, max_length=50)
    theme_ids: list[UUID] = Field(default_factory=list, max_length=50)

    @field_validator("tags", "keywords")
    @classmethod
    def clean_terms(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(item.strip() for item in value if item.strip()))

    @model_validator(mode="after")
    def dates_are_ordered(self) -> "AssetCreate":
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must not be before start_date")
        return self


class AssetUpdate(AssetCreate):
    pass


class EvidenceCreate(ApiModel):
    title: str = Field(min_length=1, max_length=250)
    description: str = Field(default="", max_length=30_000)
    source_url: str = Field(default="", max_length=1_000)
    document_id: UUID | None = None


class DocumentRead(ApiModel):
    id: UUID
    original_filename: str
    mime_type: str
    byte_size: int
    sha256: str
    ai_handling_policy: AiHandlingPolicy
    extraction_status: str
    extraction_error: str
    created_at: datetime


class EvidenceRead(EvidenceCreate):
    id: UUID
    asset_id: UUID
    source_kind: str
    created_at: datetime
    document: DocumentRead | None = None


class AssetRead(AssetCreate):
    id: UUID
    source_kind: str
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    themes: list[ThemeRead] = Field(default_factory=list)
    evidence: list[EvidenceRead] = Field(default_factory=list)
    organisation: OrganisationRead | None = None


class AssetList(ApiModel):
    items: list[AssetRead]
    total: int


class TimelineItem(ApiModel):
    id: UUID
    title: str
    category: str
    start_date: date | None
    end_date: date | None
    role: str
    organisation: str | None


class TimelineDuplicateCandidate(TimelineItem):
    description: str
    source_kind: str
    evidence_count: int


class TimelineDuplicateGroup(ApiModel):
    confidence: int = Field(ge=0, le=100)
    reasons: list[str]
    items: list[TimelineDuplicateCandidate]


class TimelineDuplicateResolution(ApiModel):
    keep_id: UUID
    archive_ids: list[UUID] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def keep_record_must_be_distinct(self) -> "TimelineDuplicateResolution":
        if self.keep_id in self.archive_ids:
            raise ValueError("The retained record cannot also be archived")
        if len(set(self.archive_ids)) != len(self.archive_ids):
            raise ValueError("Duplicate archive IDs are not allowed")
        return self


class TimelineDuplicateResolutionResult(ApiModel):
    kept_id: UUID
    archived_ids: list[UUID]


class PublicInformationConfirmation(ApiModel):
    confirmed_public_information: bool

    @model_validator(mode="after")
    def must_confirm(self) -> "PublicInformationConfirmation":
        if not self.confirmed_public_information:
            raise ValueError("Public-information confirmation is required")
        return self


class ImportRequest(PublicInformationConfirmation):
    mode: str = Field(default="dry_run", pattern="^(dry_run|apply)$")
    payload: dict[str, object]


class ImportReport(ApiModel):
    mode: str
    schema_version: str
    valid: bool
    counts: dict[str, int]
    errors: list[str]
    warnings: list[str]
    duplicate_titles: list[str]
    applied: bool


class BackupRead(ApiModel):
    filename: str
    byte_size: int
    created_at: datetime
    download_url: str
