from fastapi import APIRouter

from app.api.routes import (
    applications,
    career,
    dashboard,
    data,
    health,
    ingestion,
    opportunities,
    targets,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(dashboard.router, tags=["dashboard"])
api_router.include_router(career.router, tags=["career intelligence"])
api_router.include_router(data.router, prefix="/data", tags=["data management"])
api_router.include_router(ingestion.router, prefix="/ingestions", tags=["career ingestion"])
api_router.include_router(opportunities.router, prefix="/opportunities", tags=["opportunities"])
api_router.include_router(targets.router, prefix="/targets", tags=["targets and readiness"])
api_router.include_router(applications.router, prefix="/applications", tags=["job applications"])
