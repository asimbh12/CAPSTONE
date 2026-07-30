from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlmodel import Session, col, select

from app.db.session import get_session
from app.models.career import Fellowship
from app.schemas.fellowships import FellowshipInput, FellowshipList, FellowshipRead
from app.services.audit import record_audit
from app.services.fellowships import fellowship_read, get_or_404, touch, validate_links

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
INACTIVE_STATUSES = {"awarded", "unsuccessful", "archived"}


@router.get("", response_model=FellowshipList)
def list_fellowships(session: SessionDependency) -> FellowshipList:
    rows = list(
        session.exec(select(Fellowship).order_by(col(Fellowship.updated_at).desc())).all()
    )
    items = [fellowship_read(session, row) for row in rows if row.status != "archived"]
    return FellowshipList(
        items=items,
        total=len(items),
        active=sum(item.status not in INACTIVE_STATUSES for item in items),
        closing_soon=sum(item.deadline_status == "closing_soon" for item in items),
        sponsor_attention=sum(
            item.status not in INACTIVE_STATUSES
            and item.sponsor_status in {"not_identified", "candidate"}
            for item in items
        ),
    )


@router.post("", response_model=FellowshipRead, status_code=status.HTTP_201_CREATED)
def create_fellowship(
    payload: FellowshipInput, session: SessionDependency
) -> FellowshipRead:
    item = Fellowship(**payload.model_dump())
    validate_links(session, item)
    session.add(item)
    session.flush()
    record_audit(session, entity_type="fellowship", entity_id=item.id, action="created")
    session.commit()
    session.refresh(item)
    return fellowship_read(session, item)


@router.put("/{fellowship_id}", response_model=FellowshipRead)
def update_fellowship(
    fellowship_id: UUID, payload: FellowshipInput, session: SessionDependency
) -> FellowshipRead:
    item = get_or_404(session, fellowship_id)
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    validate_links(session, item)
    touch(item)
    session.add(item)
    record_audit(session, entity_type="fellowship", entity_id=item.id, action="updated")
    session.commit()
    session.refresh(item)
    return fellowship_read(session, item)


@router.post("/{fellowship_id}/archive", response_model=FellowshipRead)
def archive_fellowship(
    fellowship_id: UUID, session: SessionDependency
) -> FellowshipRead:
    item = get_or_404(session, fellowship_id)
    item.status = "archived"
    touch(item)
    session.add(item)
    record_audit(session, entity_type="fellowship", entity_id=item.id, action="archived")
    session.commit()
    session.refresh(item)
    return fellowship_read(session, item)
