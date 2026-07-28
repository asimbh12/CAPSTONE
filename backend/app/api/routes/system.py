from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.system import SystemReadiness
from app.services.system_readiness import build_system_readiness

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]


@router.get("/system/readiness", response_model=SystemReadiness)
def system_readiness(session: SessionDependency) -> SystemReadiness:
    return build_system_readiness(session)
