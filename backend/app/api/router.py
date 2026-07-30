from fastapi import APIRouter

from app.api.routes import (
    applications,
    awards,
    career,
    career_documents,
    dashboard,
    data,
    fellowships,
    health,
    ingestion,
    opportunities,
    system,
    targets,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(dashboard.router, tags=["dashboard"])
api_router.include_router(system.router, tags=["system readiness"])
api_router.include_router(career.router, tags=["career intelligence"])
api_router.include_router(data.router, prefix="/data", tags=["data management"])
api_router.include_router(ingestion.router, prefix="/ingestions", tags=["career ingestion"])
api_router.include_router(opportunities.router, prefix="/opportunities", tags=["opportunities"])
api_router.include_router(targets.router, prefix="/targets", tags=["targets and readiness"])
api_router.include_router(applications.router, prefix="/applications", tags=["job applications"])
api_router.include_router(
    career_documents.router, prefix="/career-documents", tags=["career documents"]
)
api_router.include_router(fellowships.router, prefix="/fellowships", tags=["fellowships"])
api_router.include_router(awards.router, prefix="/awards", tags=["awards and recognition"])
