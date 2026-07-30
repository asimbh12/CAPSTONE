from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlmodel import Session, col, select

from app.db.session import get_session
from app.models.career import AwardPathway
from app.schemas.awards import AwardInput, AwardList, AwardRead
from app.services.audit import record_audit
from app.services.awards import award_read, get_or_404, touch, validate_links

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
INACTIVE_STATUSES = {"awarded", "unsuccessful", "archived"}


@router.get("", response_model=AwardList)
def list_awards(session: SessionDependency) -> AwardList:
    rows = list(
        session.exec(select(AwardPathway).order_by(col(AwardPathway.updated_at).desc())).all()
    )
    items = [award_read(session, row) for row in rows if row.status != "archived"]
    return AwardList(
        items=items,
        total=len(items),
        active=sum(item.status not in INACTIVE_STATUSES for item in items),
        closing_soon=sum(item.deadline_status == "closing_soon" for item in items),
        nomination_attention=sum(
            item.status not in INACTIVE_STATUSES
            and item.nominator_status in {"not_identified", "candidate"}
            for item in items
        ),
    )


@router.post("", response_model=AwardRead, status_code=status.HTTP_201_CREATED)
def create_award(payload: AwardInput, session: SessionDependency) -> AwardRead:
    item = AwardPathway(**payload.model_dump())
    validate_links(session, item)
    session.add(item)
    session.flush()
    record_audit(session, entity_type="award_pathway", entity_id=item.id, action="created")
    session.commit()
    session.refresh(item)
    return award_read(session, item)


@router.put("/{award_id}", response_model=AwardRead)
def update_award(
    award_id: UUID, payload: AwardInput, session: SessionDependency
) -> AwardRead:
    item = get_or_404(session, award_id)
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    validate_links(session, item)
    touch(item)
    session.add(item)
    record_audit(session, entity_type="award_pathway", entity_id=item.id, action="updated")
    session.commit()
    session.refresh(item)
    return award_read(session, item)


@router.post("/{award_id}/archive", response_model=AwardRead)
def archive_award(award_id: UUID, session: SessionDependency) -> AwardRead:
    item = get_or_404(session, award_id)
    item.status = "archived"
    touch(item)
    session.add(item)
    record_audit(session, entity_type="award_pathway", entity_id=item.id, action="archived")
    session.commit()
    session.refresh(item)
    return award_read(session, item)
