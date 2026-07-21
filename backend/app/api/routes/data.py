from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, JSONResponse
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.career import BackupRead, ImportReport, ImportRequest
from app.services.data_management import build_export, create_backup, import_data, resolve_backup

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]


@router.get("/export")
def export_json(session: SessionDependency) -> JSONResponse:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return JSONResponse(
        content=build_export(session),
        headers={"Content-Disposition": f'attachment; filename="capstone-export-{timestamp}.json"'},
    )


@router.get("/template")
def import_template() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "profile": {
            "name": "",
            "current_title": "",
            "current_organisation": "",
            "career_mission": "",
            "career_narrative": "",
        },
        "themes": [{"name": "Example theme", "description": ""}],
        "goals": [
            {
                "title": "Example goal",
                "description": "",
                "horizon": "medium_term",
                "target_date": None,
            }
        ],
        "organisations": [],
        "people": [],
        "assets": [
            {
                "title": "Example career asset",
                "description": "",
                "category": "Leadership Asset",
                "subcategory": "",
                "start_date": None,
                "end_date": None,
                "date_precision": "day",
                "status": "active",
                "impact_summary": "",
                "organisation_id": None,
                "role": "",
                "visibility": "public",
                "tags": [],
                "keywords": [],
                "theme_ids": [],
            }
        ],
    }


@router.post("/import", response_model=ImportReport)
def import_json(payload: ImportRequest, session: SessionDependency) -> ImportReport:
    return import_data(session, payload.payload, mode=payload.mode)


@router.post("/backups", response_model=BackupRead)
def backup(session: SessionDependency) -> BackupRead:
    path = create_backup(session)
    stat = path.stat()
    return BackupRead(
        filename=path.name,
        byte_size=stat.st_size,
        created_at=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
        download_url=f"/api/data/backups/{path.name}",
    )


@router.get("/backups/{filename}")
def download_backup(filename: str) -> FileResponse:
    path = resolve_backup(filename)
    return FileResponse(path, media_type="application/zip", filename=path.name)
