from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApiModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CriterionInput(ApiModel):
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(default="", max_length=30_000)
    weight: float = Field(default=1, gt=0, le=100)
    sort_order: int = Field(default=0, ge=0)
    provenance: str = Field(default="user", pattern="^(user|ai)$")


class TargetInput(ApiModel):
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(default="", max_length=30_000)
    target_type: str = Field(default="Role", min_length=1, max_length=100)
    status: str = Field(
        default="adopted", pattern="^(suggested|adopted|paused|achieved|abandoned)$"
    )
    target_date: date | None = None
    provenance: str = Field(default="user", pattern="^(user|ai)$")
    criteria: list[CriterionInput] = Field(default_factory=list, max_length=50)


class CriterionMappingInput(ApiModel):
    asset_ids: list[UUID] = Field(default_factory=list, max_length=500)
    evidence_ids: list[UUID] = Field(default_factory=list, max_length=500)


class TargetGoalMappingInput(ApiModel):
    goal_ids: list[UUID] = Field(default_factory=list, max_length=50)


class CriterionRead(ApiModel):
    id: UUID
    title: str
    description: str
    weight: float
    sort_order: int
    provenance: str
    asset_ids: list[UUID]
    evidence_ids: list[UUID]


class CriterionAssessmentInput(ApiModel):
    criterion_id: UUID
    coverage: float = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=100)
    explanation: str = Field(default="", max_length=30_000)
    recommended_action: str = Field(default="", max_length=30_000)


class ReadinessInput(ApiModel):
    criteria: list[CriterionAssessmentInput] = Field(min_length=1, max_length=50)


class CriterionAssessmentRead(ApiModel):
    criterion_id: UUID
    criterion_title: str
    weight: float
    normalized_weight: float
    coverage: float
    confidence: float
    explanation: str
    recommended_action: str
    asset_ids: list[UUID]
    evidence_ids: list[UUID]


class ReadinessRead(ApiModel):
    id: UUID
    version: int
    algorithm_version: str
    readiness_score: float
    overall_confidence: float
    strengths: list[str]
    gaps: list[str]
    recommendations: list[str]
    criteria: list[CriterionAssessmentRead]
    created_at: datetime


class TargetRead(ApiModel):
    id: UUID
    title: str
    description: str
    target_type: str
    status: str
    target_date: date | None
    provenance: str
    goal_ids: list[UUID]
    criteria: list[CriterionRead]
    latest_assessment: ReadinessRead | None
    created_at: datetime
    updated_at: datetime


class GoalTrajectoryPoint(ApiModel):
    created_at: datetime
    readiness_score: float
    overall_confidence: float
    assessed_target_count: int


class GoalReadinessRead(ApiModel):
    goal_id: UUID
    title: str
    horizon: str
    target_date: date | None
    linked_target_ids: list[UUID]
    linked_target_titles: list[str]
    assessed_target_count: int
    readiness_score: float | None
    overall_confidence: float | None
    trend: float | None
    status: str
    trajectory: list[GoalTrajectoryPoint]
    mapped_asset_ids: list[UUID] = Field(default_factory=list)
    mapped_asset_titles: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    explanation: str = ""


class ProviderGoalAssessment(ApiModel):
    readiness_score: float = Field(default=0, ge=0, le=100)
    confidence: float = Field(default=0, ge=0, le=100)
    explanation: str = ""
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    asset_ids: list[str] = Field(default_factory=list)


class TargetSuggestion(ApiModel):
    title: str = Field(min_length=1, max_length=300)
    description: str = Field(default="", max_length=5_000)
    target_type: str = Field(default="Trajectory", max_length=100)
    rationale: str = Field(default="", max_length=5_000)
    milestones: list[str] = Field(default_factory=list, max_length=20)
    criteria: list[CriterionInput] = Field(default_factory=list, max_length=20)


class TargetSuggestionResponse(ApiModel):
    provider: str = ""
    suggestions: list[TargetSuggestion]


class ProviderCriterionSuggestion(ApiModel):
    title: str = ""
    description: str = ""
    weight: float = 1
    sort_order: int = 0
    provenance: str = "ai"


class ProviderTargetSuggestion(ApiModel):
    title: str = ""
    description: str = ""
    target_type: str = "Trajectory"
    rationale: str = ""
    milestones: list[str] = Field(default_factory=list)
    criteria: list[ProviderCriterionSuggestion] = Field(default_factory=list)


class ProviderTargetSuggestionResponse(ApiModel):
    suggestions: list[ProviderTargetSuggestion] = Field(default_factory=list)


class ProviderCriterionMapping(ApiModel):
    criterion_id: str = ""
    asset_ids: list[str] = Field(default_factory=list)
    coverage: float = 0
    confidence: float = 0
    explanation: str = ""
    recommended_action: str = ""


class ProviderTargetMappingResponse(ApiModel):
    criteria: list[ProviderCriterionMapping] = Field(default_factory=list)
