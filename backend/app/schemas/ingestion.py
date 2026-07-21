from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.career import AiHandlingPolicy


class IngestionModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProposedProfile(IngestionModel):
    name: str = ""
    current_title: str = ""
    current_organisation: str = ""
    career_narrative: str = ""
    field_sources: dict[str, list[str]] = Field(default_factory=dict)


class ProposedAsset(IngestionModel):
    title: str = Field(min_length=1, max_length=300)
    description: str = ""
    category: str = "Experience"
    role: str = ""
    organisation: str = ""
    start_date: date | None = None
    end_date: date | None = None
    impact_summary: str = ""
    tags: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    include: bool = True
    source_labels: list[str] = Field(default_factory=list)
    source_urls: list[str] = Field(default_factory=list)


class CareerExtractionProposal(IngestionModel):
    profile: ProposedProfile = Field(default_factory=ProposedProfile)
    assets: list[ProposedAsset] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    coverage: dict[str, int] = Field(default_factory=dict)
    source_diagnostics: dict[str, str | int | bool] = Field(default_factory=dict)


class ProviderProposedProfile(IngestionModel):
    name: str = ""
    current_title: str = ""
    current_organisation: str = ""
    career_narrative: str = ""


class ProviderCareerExtractionProposal(IngestionModel):
    profile: ProviderProposedProfile = Field(default_factory=ProviderProposedProfile)
    assets: list[ProposedAsset] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class UrlIngestionRequest(IngestionModel):
    url: str = Field(min_length=8, max_length=1_000)
    ai_handling_policy: AiHandlingPolicy = AiHandlingPolicy.AI_ALLOWED
    confirmed_public_information: bool


class PublicProfileSource(IngestionModel):
    url: str = Field(min_length=8, max_length=1_000)
    source_type: str = Field(default="other", max_length=50)


class MultiUrlIngestionRequest(IngestionModel):
    sources: list[PublicProfileSource] = Field(min_length=2, max_length=10)
    ai_handling_policy: AiHandlingPolicy = AiHandlingPolicy.AI_ALLOWED
    confirmed_public_information: bool


class IngestionRead(IngestionModel):
    id: UUID
    source_type: str
    source_label: str
    source_url: str
    source_manifest: list[PublicProfileSource] = Field(default_factory=list)
    document_id: UUID | None
    ai_handling_policy: AiHandlingPolicy
    provider: str
    status: str
    proposal: CareerExtractionProposal
    error_message: str
    created_at: datetime
    applied_at: datetime | None


class ApplyIngestionRequest(IngestionModel):
    proposal: CareerExtractionProposal


class ApplyIngestionResult(IngestionModel):
    profile_created: bool
    profile_fields_filled: list[str]
    assets_created: int
    assets_skipped: int
    organisations_created: int
    themes_created: int


class AiProviderStatus(IngestionModel):
    configured_provider: str
    active_provider: str
    model: str
    gemini_key_configured: bool


class AiOperationRead(IngestionModel):
    id: UUID
    operation: str
    entity_type: str
    entity_id: str
    provider: str
    model: str
    status: str
    input_characters: int
    output_characters: int
    error_message: str
    created_at: datetime


class AssetEnrichment(IngestionModel):
    tags: list[str] = Field(default_factory=list, max_length=30)
    themes: list[str] = Field(default_factory=list, max_length=20)
    summary: str = Field(default="", max_length=2_000)
    association_suggestions: list[str] = Field(default_factory=list, max_length=20)


class AssetEnrichmentResult(IngestionModel):
    asset_id: UUID
    provider: str
    tags_added: list[str]
    themes_added: list[str]
    summary: str
    association_suggestions: list[str]
