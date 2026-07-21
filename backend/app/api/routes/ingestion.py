from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlmodel import Session, col, select

from app.db.session import get_session
from app.models.career import AiHandlingPolicy, IngestionRun
from app.schemas.ingestion import (
    ApplyIngestionRequest,
    ApplyIngestionResult,
    IngestionRead,
    UrlIngestionRequest,
)
from app.services.documents import store_document
from app.services.ingestion import (
    apply_ingestion,
    create_ingestion,
    fetch_public_page,
    ingestion_read,
)

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]


@router.get("", response_model=list[IngestionRead])
def list_ingestions(session: SessionDependency) -> list[dict[str, object]]:
    runs = session.exec(select(IngestionRun).order_by(col(IngestionRun.created_at).desc())).all()
    return [ingestion_read(run) for run in runs]


@router.post("/documents", response_model=IngestionRead, status_code=status.HTTP_201_CREATED)
async def ingest_document(
    session: SessionDependency,
    file: Annotated[UploadFile, File()],
    ai_handling_policy: Annotated[AiHandlingPolicy, Form()] = AiHandlingPolicy.LOCAL_ONLY,
    confirmed_public_information: Annotated[bool, Form()] = False,
) -> dict[str, object]:
    document, _ = await store_document(
        session,
        upload=file,
        policy=ai_handling_policy,
        confirmed_public_information=confirmed_public_information,
    )
    run = create_ingestion(
        session,
        source_type="document",
        source_label=document.original_filename,
        text=document.extracted_text,
        policy=ai_handling_policy,
        document_id=document.id,
    )
    session.commit()
    session.refresh(run)
    return ingestion_read(run)


@router.post("/urls", response_model=IngestionRead, status_code=status.HTTP_201_CREATED)
def ingest_url(payload: UrlIngestionRequest, session: SessionDependency) -> dict[str, object]:
    if not payload.confirmed_public_information:
        raise HTTPException(
            status_code=422, detail="Confirm that the URL contains public professional information"
        )
    label, text = fetch_public_page(payload.url)
    run = create_ingestion(
        session,
        source_type="url",
        source_label=label,
        source_url=payload.url,
        text=text,
        policy=payload.ai_handling_policy,
    )
    session.commit()
    session.refresh(run)
    return ingestion_read(run)


@router.post("/{run_id}/apply", response_model=ApplyIngestionResult)
def apply_run(
    run_id: UUID, payload: ApplyIngestionRequest, session: SessionDependency
) -> ApplyIngestionResult:
    run = session.get(IngestionRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Ingestion proposal not found")
    result = apply_ingestion(session, run, payload.proposal)
    session.commit()
    return result
