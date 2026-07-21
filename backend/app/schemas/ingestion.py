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


class CareerExtractionProposal(IngestionModel):
    profile: ProposedProfile = Field(default_factory=ProposedProfile)
    assets: list[ProposedAsset] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class UrlIngestionRequest(IngestionModel):
    url: str = Field(min_length=8, max_length=1_000)
    ai_handling_policy: AiHandlingPolicy = AiHandlingPolicy.AI_ALLOWED
    confirmed_public_information: bool


class IngestionRead(IngestionModel):
    id: UUID
    source_type: str
    source_label: str
    source_url: str
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
