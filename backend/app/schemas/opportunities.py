from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.career import OpportunityStatus, Provenance


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class OpportunityInput(ApiModel):
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(default="", max_length=30000)
    opportunity_type: str = Field(min_length=1, max_length=100)
    organisation_id: UUID | None = None
    url: str = Field(default="", max_length=1000)
    opening_date: date | None = None
    closing_date: date | None = None
    status: OpportunityStatus = OpportunityStatus.DISCOVERED
    owner: str = Field(default="", max_length=200)
    next_action: str = Field(default="", max_length=500)
    notes: str = Field(default="", max_length=30000)
    source: str = Field(default=Provenance.USER.value, max_length=50)
    strategic_value: int = Field(ge=1, le=5)
    probability: int = Field(ge=0, le=100)
    effort: int = Field(ge=1, le=5)
    score_input_source: str = Field(default=Provenance.USER.value, pattern="^(user|ai)$")

    @model_validator(mode="after")
    def dates_are_ordered(self) -> "OpportunityInput":
        if self.opening_date and self.closing_date and self.closing_date < self.opening_date:
            raise ValueError("closing_date must not be before opening_date")
        return self


class AssessmentRead(ApiModel):
    id: UUID
    algorithm_version: str
    strategic_value: int
    probability: int
    effort: int
    raw_score: float
    normalized_score: float
    input_source: str
    explanation: str
    created_at: datetime


class UrgencyRead(ApiModel):
    level: str
    days_remaining: int | None
    label: str


class OpportunityRead(ApiModel):
    id: UUID
    title: str
    description: str
    opportunity_type: str
    organisation_id: UUID | None
    organisation_name: str | None
    url: str
    opening_date: date | None
    closing_date: date | None
    status: str
    owner: str
    next_action: str
    notes: str
    source: str
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    assessment: AssessmentRead
    urgency: UrgencyRead


class OpportunityList(ApiModel):
    items: list[OpportunityRead]
    total: int


class OpportunitySummary(ApiModel):
    active: int
    pursuing: int
    closing_soon: int
    top_opportunity: OpportunityRead | None
