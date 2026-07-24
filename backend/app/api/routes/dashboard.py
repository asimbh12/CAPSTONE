from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.dashboard import DashboardRead
from app.services.dashboard import build_dashboard

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]


@router.get("/dashboard", response_model=DashboardRead)
def dashboard(session: SessionDependency) -> DashboardRead:
    return build_dashboard(session)
