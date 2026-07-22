from datetime import UTC, datetime
from io import BytesIO
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.career import AiHandlingPolicy, ApplicationRequirement, JobApplication
from app.schemas.applications import (
    ApplicationInput,
    ApplicationList,
    ApplicationRead,
    RequirementsUpdate,
)
from app.services.applications import (
    build_read,
    export_pack,
    extract_requirements,
    generate_drafts,
    get_or_404,
    map_and_assess,
)
from app.services.audit import record_audit
from app.services.documents import store_document

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]


def _replace_requirements(
    session: Session, item: JobApplication, payload: RequirementsUpdate
) -> None:
    for row in session.exec(
        select(ApplicationRequirement).where(ApplicationRequirement.application_id == item.id)
    ).all():
        session.delete(row)
    for index, requirement in enumerate(payload.requirements):
        session.add(
            ApplicationRequirement(
                application_id=item.id,
                sort_order=index,
                **requirement.model_dump(),
            )
        )
    item.requirements_confirmed = payload.confirmed
    item.updated_at = datetime.now(UTC)
    session.add(item)


@router.get("", response_model=ApplicationList)
def list_applications(session: SessionDependency) -> ApplicationList:
    items = list(session.exec(select(JobApplication)).all())
    items.sort(key=lambda item: item.updated_at, reverse=True)
    return ApplicationList(items=[build_read(session, item) for item in items], total=len(items))


@router.post("", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
def create_application(payload: ApplicationInput, session: SessionDependency) -> ApplicationRead:
    if not payload.confirmed_public_information:
        raise HTTPException(
            status_code=422,
            detail=(
                "Confirm that the position description contains only public "
                "professional information"
            ),
        )
    item = JobApplication(**payload.model_dump(exclude={"confirmed_public_information"}))
    session.add(item)
    session.flush()
    requirements = extract_requirements(item.position_description)
    _replace_requirements(session, item, RequirementsUpdate(requirements=requirements))
    record_audit(session, entity_type="job_application", entity_id=item.id, action="created")
    session.commit()
    session.refresh(item)
    return build_read(session, item)


@router.post("/documents", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
async def create_from_document(
    session: SessionDependency,
    role_title: Annotated[str, Form(min_length=1, max_length=300)],
    file: Annotated[UploadFile, File()],
    organisation: Annotated[str, Form(max_length=250)] = "",
    confirmed_public_information: Annotated[bool, Form()] = False,
) -> ApplicationRead:
    document, _ = await store_document(
        session,
        upload=file,
        policy=AiHandlingPolicy.AI_ALLOWED,
        confirmed_public_information=confirmed_public_information,
    )
    if len(document.extracted_text.strip()) < 20:
        raise HTTPException(
            status_code=422, detail="The document did not contain enough extractable text"
        )
    item = JobApplication(
        role_title=role_title,
        organisation=organisation,
        position_description=document.extracted_text[:150_000],
        document_id=document.id,
    )
    session.add(item)
    session.flush()
    _replace_requirements(
        session,
        item,
        RequirementsUpdate(requirements=extract_requirements(item.position_description)),
    )
    record_audit(
        session, entity_type="job_application", entity_id=item.id, action="created_from_document"
    )
    session.commit()
    session.refresh(item)
    return build_read(session, item)


@router.get("/{application_id}", response_model=ApplicationRead)
def get_application(application_id: UUID, session: SessionDependency) -> ApplicationRead:
    return build_read(session, get_or_404(session, application_id))


@router.put("/{application_id}/requirements", response_model=ApplicationRead)
def update_requirements(
    application_id: UUID, payload: RequirementsUpdate, session: SessionDependency
) -> ApplicationRead:
    item = get_or_404(session, application_id)
    _replace_requirements(session, item, payload)
    record_audit(
        session,
        entity_type="job_application",
        entity_id=item.id,
        action="requirements_reviewed",
        details={"confirmed": payload.confirmed},
    )
    session.commit()
    session.refresh(item)
    return build_read(session, item)


@router.post("/{application_id}/assess", response_model=ApplicationRead)
def assess(application_id: UUID, session: SessionDependency) -> ApplicationRead:
    item = get_or_404(session, application_id)
    map_and_assess(session, item)
    item.status = "assessed"
    item.updated_at = datetime.now(UTC)
    session.add(item)
    record_audit(
        session, entity_type="job_application", entity_id=item.id, action="evidence_mapped"
    )
    session.commit()
    return build_read(session, item)


@router.post("/{application_id}/drafts", response_model=ApplicationRead)
def drafts(application_id: UUID, session: SessionDependency) -> ApplicationRead:
    item = get_or_404(session, application_id)
    generate_drafts(session, item)
    item.status = "drafted"
    item.updated_at = datetime.now(UTC)
    session.add(item)
    record_audit(
        session, entity_type="job_application", entity_id=item.id, action="drafts_generated"
    )
    session.commit()
    return build_read(session, item)


@router.get("/{application_id}/export/{format_name}")
def export(application_id: UUID, format_name: str, session: SessionDependency) -> StreamingResponse:
    if format_name not in {"docx", "pdf"}:
        raise HTTPException(status_code=422, detail="Export format must be docx or pdf")
    item = get_or_404(session, application_id)
    content = export_pack(session, item, format_name)
    media_type = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if format_name == "docx"
        else "application/pdf"
    )
    filename = f"{item.role_title[:80].strip().replace(' ', '-')}-application-pack.{format_name}"
    return StreamingResponse(
        BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
