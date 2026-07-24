from pydantic import BaseModel, Field

from app.schemas.career import AssetRead


class DashboardMetrics(BaseModel):
    active_assets: int
    asset_categories: int
    strategic_goals: int
    timeline_events: int
    open_opportunities: int
    closing_soon: int


class DashboardAction(BaseModel):
    key: str
    title: str
    description: str
    page: str
    priority: int = Field(ge=1, le=100)
    count: int = Field(default=0, ge=0)
    urgency: str = Field(pattern="^(critical|high|medium|low)$")


class DashboardRead(BaseModel):
    profile_name: str
    metrics: DashboardMetrics
    actions: list[DashboardAction]
    recent_assets: list[AssetRead]
