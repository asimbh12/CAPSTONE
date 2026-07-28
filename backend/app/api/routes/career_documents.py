from datetime import UTC, datetime
from io import BytesIO
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session, col, select

from app.db.session import get_session
from app.models.career import CareerDocument
from app.schemas.career_documents import (
    CareerDocumentGenerate,
    CareerDocumentList,
    CareerDocumentRead,
    CareerDocumentUpdate,
)
from app.services.audit import record_audit
from app.services.career_documents import export_document, generate, get_or_404, read_document

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]


@router.get("", response_model=CareerDocumentList)
def list_documents(session: SessionDependency) -> CareerDocumentList:
    items = list(
        session.exec(select(CareerDocument).order_by(col(CareerDocument.updated_at).desc())).all()
    )
    return CareerDocumentList(items=[read_document(item) for item in items], total=len(items))


@router.post("", response_model=CareerDocumentRead, status_code=status.HTTP_201_CREATED)
def generate_document(
    payload: CareerDocumentGenerate, session: SessionDependency
) -> CareerDocumentRead:
    item = generate(session, payload)
    session.flush()
    record_audit(
        session,
        entity_type="career_document",
        entity_id=item.id,
        action="generated",
        source="ai" if item.provider == "gemini" else "rule",
        details={"document_type": item.document_type, "provider": item.provider},
    )
    session.commit()
    session.refresh(item)
    return read_document(item)


@router.put("/{document_id}", response_model=CareerDocumentRead)
def update_document(
    document_id: UUID, payload: CareerDocumentUpdate, session: SessionDependency
) -> CareerDocumentRead:
    item = get_or_404(session, document_id)
    item.title = payload.title
    item.content = payload.content
    item.updated_at = datetime.now(UTC)
    session.add(item)
    record_audit(
        session, entity_type="career_document", entity_id=item.id, action="edited"
    )
    session.commit()
    session.refresh(item)
    return read_document(item)


@router.get("/{document_id}/export/{format_name}")
def export(
    document_id: UUID, format_name: str, session: SessionDependency
) -> StreamingResponse:
    if format_name not in {"docx", "pdf"}:
        raise HTTPException(status_code=422, detail="Export format must be docx or pdf")
    item = get_or_404(session, document_id)
    content = export_document(item, format_name)
    media_type = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if format_name == "docx"
        else "application/pdf"
    )
    filename = f"{item.title[:80].strip().replace(' ', '-')}.{format_name}"
    return StreamingResponse(
        BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
