from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlmodel import Session

from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter()
SettingsDependency = Annotated[Settings, Depends(get_settings)]
SessionDependency = Annotated[Session, Depends(get_session)]


@router.get("/health", response_model=HealthResponse)
def health(settings: SettingsDependency) -> HealthResponse:
    return HealthResponse(
        status="ok", service="api", version=settings.app_version, environment=settings.environment
    )


@router.get("/health/ready", response_model=ReadinessResponse)
def readiness(session: SessionDependency) -> ReadinessResponse:
    session.execute(text("SELECT 1"))
    return ReadinessResponse(status="ready", checks={"database": "ok"})
