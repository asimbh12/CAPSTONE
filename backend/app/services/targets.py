import json
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, col, select

from app.models.career import (
    CareerAsset,
    CriterionAssessment,
    CriterionAssetLink,
    CriterionEvidenceLink,
    EvidenceItem,
    ReadinessAssessment,
    Target,
    TargetCriterion,
)
from app.schemas.targets import (
    CriterionAssessmentRead,
    CriterionRead,
    ReadinessInput,
    ReadinessRead,
    TargetRead,
)

ALGORITHM_VERSION = "target-readiness-v1"


def get_target_or_404(session: Session, target_id: UUID) -> Target:
    target = session.get(Target, target_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Target not found")
    return target


def get_criterion_or_404(session: Session, criterion_id: UUID) -> TargetCriterion:
    criterion = session.get(TargetCriterion, criterion_id)
    if criterion is None:
        raise HTTPException(status_code=404, detail="Target criterion not found")
    return criterion


def criterion_read(session: Session, criterion: TargetCriterion) -> CriterionRead:
    asset_ids = list(
        session.exec(
            select(CriterionAssetLink.asset_id).where(
                CriterionAssetLink.criterion_id == criterion.id
            )
        ).all()
    )
    evidence_ids = list(
        session.exec(
            select(CriterionEvidenceLink.evidence_id).where(
                CriterionEvidenceLink.criterion_id == criterion.id
            )
        ).all()
    )
    return CriterionRead(**criterion.model_dump(), asset_ids=asset_ids, evidence_ids=evidence_ids)


def readiness_read(session: Session, assessment: ReadinessAssessment) -> ReadinessRead:
    rows = session.exec(
        select(CriterionAssessment)
        .where(CriterionAssessment.readiness_assessment_id == assessment.id)
        .order_by(col(CriterionAssessment.normalized_weight).desc())
    ).all()
    return ReadinessRead(
        **assessment.model_dump(),
        strengths=json.loads(assessment.strengths_json),
        gaps=json.loads(assessment.gaps_json),
        recommendations=json.loads(assessment.recommendations_json),
        criteria=[
            CriterionAssessmentRead(
                **row.model_dump(),
                asset_ids=json.loads(row.asset_ids_json),
                evidence_ids=json.loads(row.evidence_ids_json),
            )
            for row in rows
        ],
    )


def latest_readiness(session: Session, target_id: UUID) -> ReadinessRead | None:
    assessment = session.exec(
        select(ReadinessAssessment)
        .where(ReadinessAssessment.target_id == target_id)
        .order_by(
            col(ReadinessAssessment.version).desc(), col(ReadinessAssessment.created_at).desc()
        )
    ).first()
    return readiness_read(session, assessment) if assessment else None


def target_read(session: Session, target: Target) -> TargetRead:
    criteria = session.exec(
        select(TargetCriterion)
        .where(TargetCriterion.target_id == target.id)
        .order_by(col(TargetCriterion.sort_order), col(TargetCriterion.created_at))
    ).all()
    return TargetRead(
        **target.model_dump(),
        criteria=[criterion_read(session, criterion) for criterion in criteria],
        latest_assessment=latest_readiness(session, target.id),
    )


def replace_mappings(
    session: Session,
    criterion: TargetCriterion,
    asset_ids: list[UUID],
    evidence_ids: list[UUID],
) -> None:
    for asset_id in asset_ids:
        if session.get(CareerAsset, asset_id) is None:
            raise HTTPException(status_code=422, detail=f"Career asset {asset_id} does not exist")
    for evidence_id in evidence_ids:
        if session.get(EvidenceItem, evidence_id) is None:
            raise HTTPException(status_code=422, detail=f"Evidence {evidence_id} does not exist")
    for link in session.exec(
        select(CriterionAssetLink).where(CriterionAssetLink.criterion_id == criterion.id)
    ).all():
        session.delete(link)
    for link in session.exec(
        select(CriterionEvidenceLink).where(CriterionEvidenceLink.criterion_id == criterion.id)
    ).all():
        session.delete(link)
    for asset_id in dict.fromkeys(asset_ids):
        session.add(CriterionAssetLink(criterion_id=criterion.id, asset_id=asset_id))
    for evidence_id in dict.fromkeys(evidence_ids):
        session.add(CriterionEvidenceLink(criterion_id=criterion.id, evidence_id=evidence_id))


def assess_target(session: Session, target: Target, payload: ReadinessInput) -> ReadinessAssessment:
    criteria = {
        item.id: item
        for item in session.exec(
            select(TargetCriterion).where(TargetCriterion.target_id == target.id)
        ).all()
    }
    submitted = {item.criterion_id: item for item in payload.criteria}
    if not criteria or set(criteria) != set(submitted):
        raise HTTPException(status_code=422, detail="Assess every current criterion exactly once")
    total_weight = sum(item.weight for item in criteria.values())
    previous = session.exec(
        select(ReadinessAssessment)
        .where(ReadinessAssessment.target_id == target.id)
        .order_by(col(ReadinessAssessment.version).desc())
    ).first()
    version = previous.version + 1 if previous else 1
    readiness = sum(
        criteria[item.criterion_id].weight / total_weight * item.coverage
        for item in payload.criteria
    )
    confidence = sum(
        criteria[item.criterion_id].weight / total_weight * item.confidence
        for item in payload.criteria
    )
    strengths = [
        criteria[item.criterion_id].title for item in payload.criteria if item.coverage >= 70
    ]
    gaps = [criteria[item.criterion_id].title for item in payload.criteria if item.coverage < 50]
    recommendations = list(
        dict.fromkeys(
            item.recommended_action for item in payload.criteria if item.recommended_action
        )
    )
    assessment = ReadinessAssessment(
        target_id=target.id,
        version=version,
        readiness_score=round(readiness, 1),
        overall_confidence=round(confidence, 1),
        strengths_json=json.dumps(strengths),
        gaps_json=json.dumps(gaps),
        recommendations_json=json.dumps(recommendations),
    )
    session.add(assessment)
    session.flush()
    for item in payload.criteria:
        criterion = criteria[item.criterion_id]
        assets = list(
            session.exec(
                select(CriterionAssetLink.asset_id).where(
                    CriterionAssetLink.criterion_id == criterion.id
                )
            ).all()
        )
        evidence = list(
            session.exec(
                select(CriterionEvidenceLink.evidence_id).where(
                    CriterionEvidenceLink.criterion_id == criterion.id
                )
            ).all()
        )
        session.add(
            CriterionAssessment(
                readiness_assessment_id=assessment.id,
                criterion_id=criterion.id,
                criterion_title=criterion.title,
                weight=criterion.weight,
                normalized_weight=round(criterion.weight / total_weight, 6),
                coverage=item.coverage,
                confidence=item.confidence,
                explanation=item.explanation,
                recommended_action=item.recommended_action,
                asset_ids_json=json.dumps([str(value) for value in assets]),
                evidence_ids_json=json.dumps([str(value) for value in evidence]),
            )
        )
    return assessment
