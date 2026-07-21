from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, col, select

from app.models.career import Opportunity, OpportunityAssessment, Organisation
from app.schemas.opportunities import AssessmentRead, OpportunityRead, UrgencyRead

ALGORITHM_VERSION = "opportunity-priority-v1"


def score(value: int, probability: int, effort: int) -> tuple[float, float, str]:
    v, p, e = Decimal(value), Decimal(probability), Decimal(effort)
    raw = (v * (p / Decimal(100)) / e).quantize(Decimal("0.0001"), ROUND_HALF_UP)
    normalized = (v * p / (Decimal(5) * e)).quantize(Decimal("0.1"), ROUND_HALF_UP)
    explanation = (
        f"({value} strategic value × {probability}% probability) ÷ {effort} effort; "
        f"normalized to {normalized}/100."
    )
    return float(raw), float(normalized), explanation


def add_assessment(
    session: Session, opportunity_id: UUID, value: int, probability: int, effort: int, source: str
) -> OpportunityAssessment:
    raw, normalized, explanation = score(value, probability, effort)
    assessment = OpportunityAssessment(
        opportunity_id=opportunity_id,
        strategic_value=value,
        probability=probability,
        effort=effort,
        raw_score=raw,
        normalized_score=normalized,
        input_source=source,
        explanation=explanation,
    )
    session.add(assessment)
    return assessment


def latest_assessment(session: Session, opportunity_id: UUID) -> OpportunityAssessment:
    result = session.exec(
        select(OpportunityAssessment)
        .where(OpportunityAssessment.opportunity_id == opportunity_id)
        .order_by(
            col(OpportunityAssessment.created_at).desc(), col(OpportunityAssessment.id).desc()
        )
    ).first()
    if result is None:
        raise HTTPException(status_code=500, detail="Opportunity has no assessment")
    return result


def urgency(closing_date: date | None) -> UrgencyRead:
    if closing_date is None:
        return UrgencyRead(level="none", days_remaining=None, label="No deadline")
    days = (closing_date - date.today()).days
    if days < 0:
        level, label = "overdue", f"Overdue by {abs(days)} days"
    elif days <= 3:
        level, label = "critical", f"Closes in {days} days"
    elif days <= 7:
        level, label = "high", f"Closes in {days} days"
    elif days <= 30:
        level, label = "medium", f"Closes in {days} days"
    else:
        level, label = "low", f"Closes in {days} days"
    return UrgencyRead(level=level, days_remaining=days, label=label)


def build_read(session: Session, item: Opportunity) -> OpportunityRead:
    assessment = latest_assessment(session, item.id)
    organisation = session.get(Organisation, item.organisation_id) if item.organisation_id else None
    return OpportunityRead(
        **item.model_dump(),
        organisation_name=organisation.name if organisation else None,
        assessment=AssessmentRead.model_validate(assessment),
        urgency=urgency(item.closing_date),
    )


def get_or_404(session: Session, opportunity_id: UUID) -> Opportunity:
    item = session.get(Opportunity, opportunity_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return item
