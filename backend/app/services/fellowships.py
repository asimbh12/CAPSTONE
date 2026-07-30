import json
from datetime import UTC, date, datetime

from fastapi import HTTPException
from sqlmodel import Session, col, select

from app.models.career import Fellowship, ReadinessAssessment, Target
from app.schemas.fellowships import FellowshipRead


def get_or_404(session: Session, fellowship_id: object) -> Fellowship:
    item = session.get(Fellowship, fellowship_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Fellowship not found")
    return item


def fellowship_read(session: Session, item: Fellowship) -> FellowshipRead:
    target = session.get(Target, item.target_id) if item.target_id else None
    assessment = (
        session.exec(
            select(ReadinessAssessment)
            .where(ReadinessAssessment.target_id == item.target_id)
            .order_by(col(ReadinessAssessment.version).desc())
        ).first()
        if item.target_id
        else None
    )
    days_remaining = (item.deadline - date.today()).days if item.deadline else None
    if days_remaining is None:
        deadline_status = "not_set"
    elif days_remaining < 0:
        deadline_status = "overdue"
    elif days_remaining <= 30:
        deadline_status = "closing_soon"
    else:
        deadline_status = "scheduled"
    return FellowshipRead(
        **item.model_dump(),
        readiness_score=assessment.readiness_score if assessment else None,
        readiness_confidence=assessment.overall_confidence if assessment else None,
        readiness_version=assessment.version if assessment else None,
        target_title=target.title if target else "",
        strengths=json.loads(assessment.strengths_json) if assessment else [],
        gaps=json.loads(assessment.gaps_json) if assessment else [],
        recommendations=json.loads(assessment.recommendations_json) if assessment else [],
        days_remaining=days_remaining,
        deadline_status=deadline_status,
    )


def validate_links(session: Session, item: Fellowship) -> None:
    if item.target_id and session.get(Target, item.target_id) is None:
        raise HTTPException(status_code=422, detail="Selected readiness target does not exist")
    if item.opportunity_id:
        from app.models.career import Opportunity

        if session.get(Opportunity, item.opportunity_id) is None:
            raise HTTPException(status_code=422, detail="Selected opportunity does not exist")


def touch(item: Fellowship) -> None:
    item.updated_at = datetime.now(UTC)
