from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AwardInput(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    organisation: str = Field(default="", max_length=250)
    award_type: str = Field(
        default="custom",
        pattern="^(eureka|clunies_ross|research_australia|prime_ministers|industry|custom)$",
    )
    website: str = Field(default="", max_length=1_000)
    deadline: date | None = None
    status: str = Field(
        default="exploring",
        pattern="^(exploring|preparing|seeking_nominator|ready|submitted|awarded|unsuccessful|paused|archived)$",
    )
    target_id: UUID | None = None
    opportunity_id: UUID | None = None
    nominator_name: str = Field(default="", max_length=250)
    nominator_status: str = Field(
        default="not_identified",
        pattern="^(not_identified|candidate|approached|confirmed|not_required)$",
    )
    dossier_status: str = Field(
        default="not_started",
        pattern="^(not_started|evidence_review|drafting|review|complete)$",
    )
    next_action: str = Field(default="", max_length=500)
    notes: str = Field(default="", max_length=30_000)


class AwardRead(AwardInput):
    id: UUID
    readiness_score: float | None
    readiness_confidence: float | None
    readiness_version: int | None
    target_title: str
    strengths: list[str]
    gaps: list[str]
    recommendations: list[str]
    days_remaining: int | None
    deadline_status: str
    created_at: datetime
    updated_at: datetime


class AwardList(BaseModel):
    items: list[AwardRead]
    total: int
    active: int
    closing_soon: int
    nomination_attention: int
