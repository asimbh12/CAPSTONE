from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ApplicationInput(BaseModel):
    role_title: str = Field(min_length=1, max_length=300)
    organisation: str = Field(default="", max_length=250)
    position_description: str = Field(min_length=20, max_length=150_000)
    source_url: str = Field(default="", max_length=1000)
    confirmed_public_information: bool


class RequirementInput(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(default="", max_length=5_000)
    requirement_type: str = Field(default="essential", pattern="^(essential|desirable)$")
    weight: float = Field(default=1, ge=0.1, le=5)


class RequirementsUpdate(BaseModel):
    requirements: list[RequirementInput] = Field(min_length=1, max_length=50)
    confirmed: bool = False


class RequirementsProposal(BaseModel):
    requirements: list[RequirementInput] = Field(min_length=1, max_length=50)


class RequirementRead(RequirementInput):
    id: UUID
    asset_ids: list[UUID]
    coverage: float
    confidence: float
    explanation: str
    sort_order: int


class AssessmentRead(BaseModel):
    id: UUID
    version: int
    fit_score: float
    overall_confidence: float
    strengths: list[str]
    gaps: list[str]
    recommendations: list[str]
    created_at: datetime


class DraftRead(BaseModel):
    id: UUID
    draft_type: str
    content: str
    unsupported_claims: list[str]
    provider: str
    created_at: datetime


class ProviderApplicationDrafts(BaseModel):
    cover_letter: str = Field(min_length=300, max_length=30_000)
    selection_criteria: str = Field(min_length=300, max_length=60_000)
    tailored_cv: str = Field(min_length=300, max_length=60_000)
    interview_notes: str = Field(min_length=300, max_length=40_000)
    unsupported_claims: list[str] = Field(default_factory=list, max_length=50)


class ApplicationRead(BaseModel):
    id: UUID
    role_title: str
    organisation: str
    position_description: str
    source_url: str
    document_id: UUID | None
    status: str
    requirements_confirmed: bool
    created_at: datetime
    updated_at: datetime
    requirements: list[RequirementRead]
    assessment: AssessmentRead | None
    drafts: list[DraftRead]


class ApplicationList(BaseModel):
    items: list[ApplicationRead]
    total: int
