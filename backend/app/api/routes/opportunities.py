from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, col, select

from app.db.session import get_session
from app.models.career import Opportunity, OpportunityAssessment, OpportunityStatus, Organisation
from app.schemas.opportunities import (
    AssessmentRead,
    OpportunityInput,
    OpportunityList,
    OpportunityRead,
    OpportunitySummary,
)
from app.services.audit import record_audit
from app.services.opportunities import add_assessment, build_read, get_or_404

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]
TERMINAL = {"won", "lost", "declined", "expired", "archived"}


def _records(session: Session) -> list[OpportunityRead]:
    return [build_read(session, item) for item in session.exec(select(Opportunity)).all()]


@router.get("/summary", response_model=OpportunitySummary)
def summary(session: SessionDependency) -> OpportunitySummary:
    records = [item for item in _records(session) if item.status not in TERMINAL]
    ranked = sorted(
        records,
        key=lambda item: (
            -item.assessment.normalized_score,
            item.closing_date or datetime.max.date(),
        ),
    )
    return OpportunitySummary(
        active=len(records),
        pursuing=sum(item.status in {"pursuing", "submitted"} for item in records),
        closing_soon=sum(
            item.urgency.days_remaining is not None and 0 <= item.urgency.days_remaining <= 14
            for item in records
        ),
        top_opportunity=ranked[0] if ranked else None,
    )


@router.get("", response_model=OpportunityList)
def list_opportunities(
    session: SessionDependency,
    search: str | None = Query(default=None, max_length=200),
    opportunity_type: str | None = Query(default=None, max_length=100),
    opportunity_status: OpportunityStatus | None = None,
    include_archived: bool = False,
) -> OpportunityList:
    records = _records(session)
    if not include_archived:
        records = [item for item in records if item.status != "archived"]
    if search:
        needle = search.casefold()
        records = [
            item
            for item in records
            if needle
            in f"{item.title} {item.description} {item.organisation_name or ''}".casefold()
        ]
    if opportunity_type:
        records = [item for item in records if item.opportunity_type == opportunity_type]
    if opportunity_status:
        records = [item for item in records if item.status == opportunity_status.value]
    records.sort(
        key=lambda item: (
            -item.assessment.normalized_score,
            item.closing_date or datetime.max.date(),
            item.title.casefold(),
        )
    )
    return OpportunityList(items=records, total=len(records))


@router.post("", response_model=OpportunityRead, status_code=status.HTTP_201_CREATED)
def create_opportunity(payload: OpportunityInput, session: SessionDependency) -> OpportunityRead:
    if payload.organisation_id and session.get(Organisation, payload.organisation_id) is None:
        raise HTTPException(status_code=422, detail="Organisation does not exist")
    data = payload.model_dump(
        exclude={"strategic_value", "probability", "effort", "score_input_source"}
    )
    item = Opportunity(**data)
    session.add(item)
    session.flush()
    add_assessment(
        session,
        item.id,
        payload.strategic_value,
        payload.probability,
        payload.effort,
        payload.score_input_source,
    )
    record_audit(
        session,
        entity_type="opportunity",
        entity_id=item.id,
        action="created",
        details={"algorithm_version": "opportunity-priority-v1"},
    )
    session.commit()
    session.refresh(item)
    return build_read(session, item)


@router.get("/{opportunity_id}", response_model=OpportunityRead)
def get_opportunity(opportunity_id: UUID, session: SessionDependency) -> OpportunityRead:
    return build_read(session, get_or_404(session, opportunity_id))


@router.put("/{opportunity_id}", response_model=OpportunityRead)
def update_opportunity(
    opportunity_id: UUID, payload: OpportunityInput, session: SessionDependency
) -> OpportunityRead:
    item = get_or_404(session, opportunity_id)
    if payload.organisation_id and session.get(Organisation, payload.organisation_id) is None:
        raise HTTPException(status_code=422, detail="Organisation does not exist")
    previous_status = item.status
    for key, value in payload.model_dump(
        exclude={"strategic_value", "probability", "effort", "score_input_source"}
    ).items():
        setattr(item, key, value)
    item.updated_at = datetime.now(UTC)
    session.add(item)
    add_assessment(
        session,
        item.id,
        payload.strategic_value,
        payload.probability,
        payload.effort,
        payload.score_input_source,
    )
    record_audit(
        session,
        entity_type="opportunity",
        entity_id=item.id,
        action="updated",
        details={"previous_status": previous_status, "status": item.status},
    )
    session.commit()
    session.refresh(item)
    return build_read(session, item)


@router.post("/{opportunity_id}/archive", response_model=OpportunityRead)
def archive_opportunity(opportunity_id: UUID, session: SessionDependency) -> OpportunityRead:
    item = get_or_404(session, opportunity_id)
    item.status = "archived"
    item.archived_at = datetime.now(UTC)
    item.updated_at = datetime.now(UTC)
    session.add(item)
    record_audit(session, entity_type="opportunity", entity_id=item.id, action="archived")
    session.commit()
    session.refresh(item)
    return build_read(session, item)


@router.get("/{opportunity_id}/assessments", response_model=list[AssessmentRead])
def assessment_history(
    opportunity_id: UUID, session: SessionDependency
) -> list[OpportunityAssessment]:
    get_or_404(session, opportunity_id)
    return list(
        session.exec(
            select(OpportunityAssessment)
            .where(OpportunityAssessment.opportunity_id == opportunity_id)
            .order_by(col(OpportunityAssessment.created_at).desc())
        ).all()
    )
