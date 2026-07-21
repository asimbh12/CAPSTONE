from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlmodel import Session, col, select

from app.core.config import get_settings
from app.db.session import get_session
from app.models.career import AiHandlingPolicy, AiOperation, CareerAsset, IngestionRun
from app.schemas.ingestion import (
    AiOperationRead,
    AiProviderStatus,
    ApplyIngestionRequest,
    ApplyIngestionResult,
    AssetEnrichmentResult,
    CareerExtractionProposal,
    IngestionRead,
    MultiUrlIngestionRequest,
    PublicProfileSource,
    UrlIngestionRequest,
)
from app.services.documents import store_document
from app.services.ingestion import (
    apply_ingestion,
    build_profile_source_manifest,
    create_ingestion,
    create_multi_url_ingestion,
    enrich_asset,
    ingestion_read,
    reprocess_ingestion,
    save_proposal,
)

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]


@router.get("/provider-status", response_model=AiProviderStatus)
def provider_status() -> AiProviderStatus:
    settings = get_settings()
    gemini_ready = bool(settings.gemini_api_key)
    active = (
        "gemini" if settings.ai_provider.lower() == "gemini" and gemini_ready else "deterministic"
    )
    return AiProviderStatus(
        configured_provider=settings.ai_provider,
        active_provider=active,
        model=settings.gemini_model if active == "gemini" else "",
        gemini_key_configured=gemini_ready,
    )


@router.get("/operations", response_model=list[AiOperationRead])
def list_operations(session: SessionDependency) -> list[AiOperation]:
    return list(
        session.exec(
            select(AiOperation).order_by(col(AiOperation.created_at).desc()).limit(100)
        ).all()
    )


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
    submitted = PublicProfileSource(url=payload.url, source_type="other")
    expanded_sources = build_profile_source_manifest(submitted)
    run = create_multi_url_ingestion(
        session, sources=expanded_sources, policy=payload.ai_handling_policy
    )
    session.commit()
    session.refresh(run)
    return ingestion_read(run)


@router.post("/url-collections", response_model=IngestionRead, status_code=status.HTTP_201_CREATED)
def ingest_url_collection(
    payload: MultiUrlIngestionRequest, session: SessionDependency
) -> dict[str, object]:
    if not payload.confirmed_public_information:
        raise HTTPException(
            status_code=422, detail="Confirm that all URLs contain public professional information"
        )
    if len({item.url for item in payload.sources}) != len(payload.sources):
        raise HTTPException(status_code=422, detail="Remove duplicate URLs before analysis")
    expanded: list[PublicProfileSource] = []
    for source in payload.sources:
        expanded.extend(build_profile_source_manifest(source))
    deduplicated = list({source.url: source for source in expanded}.values())[:20]
    run = create_multi_url_ingestion(
        session, sources=deduplicated, policy=payload.ai_handling_policy
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


@router.put("/{run_id}/proposal", response_model=IngestionRead)
def correct_proposal(
    run_id: UUID, payload: CareerExtractionProposal, session: SessionDependency
) -> dict[str, object]:
    run = session.get(IngestionRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Ingestion proposal not found")
    save_proposal(session, run, payload)
    session.commit()
    session.refresh(run)
    return ingestion_read(run)


@router.post("/{run_id}/reprocess", response_model=IngestionRead)
def reprocess_run(run_id: UUID, session: SessionDependency) -> dict[str, object]:
    run = session.get(IngestionRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Ingestion proposal not found")
    reprocess_ingestion(session, run)
    session.commit()
    session.refresh(run)
    return ingestion_read(run)


@router.post("/{run_id}/suppress", response_model=IngestionRead)
def suppress_run(run_id: UUID, session: SessionDependency) -> dict[str, object]:
    run = session.get(IngestionRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Ingestion proposal not found")
    if run.status == "applied":
        raise HTTPException(status_code=409, detail="Applied ingestions cannot be suppressed")
    run.status = "suppressed"
    session.add(run)
    session.commit()
    session.refresh(run)
    return ingestion_read(run)


@router.post("/assets/{asset_id}/enrich", response_model=AssetEnrichmentResult)
def enrich_career_asset(asset_id: UUID, session: SessionDependency) -> AssetEnrichmentResult:
    asset = session.get(CareerAsset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="Career asset not found")
    result = enrich_asset(session, asset)
    session.commit()
    return result
