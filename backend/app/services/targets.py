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
    StrategicGoal,
    StrategicGoalAssessment,
    Target,
    TargetCriterion,
    TargetGoalLink,
)
from app.schemas.targets import (
    CriterionAssessmentRead,
    CriterionRead,
    GoalReadinessRead,
    GoalTrajectoryPoint,
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
        goal_ids=list(
            session.exec(
                select(TargetGoalLink.goal_id).where(TargetGoalLink.target_id == target.id)
            ).all()
        ),
        criteria=[criterion_read(session, criterion) for criterion in criteria],
        latest_assessment=latest_readiness(session, target.id),
    )


def replace_target_goals(session: Session, target: Target, goal_ids: list[UUID]) -> None:
    unique_ids = list(dict.fromkeys(goal_ids))
    if unique_ids:
        goals = session.exec(
            select(StrategicGoal).where(col(StrategicGoal.id).in_(unique_ids))
        ).all()
        if len(goals) != len(unique_ids):
            raise HTTPException(status_code=422, detail="One or more strategic goals do not exist")
    existing = session.exec(
        select(TargetGoalLink).where(TargetGoalLink.target_id == target.id)
    ).all()
    existing_by_goal = {link.goal_id: link for link in existing}
    for goal_id, link in existing_by_goal.items():
        if goal_id not in unique_ids:
            session.delete(link)
    for goal_id in unique_ids:
        if goal_id not in existing_by_goal:
            session.add(TargetGoalLink(target_id=target.id, goal_id=goal_id))


def goal_readiness(session: Session) -> list[GoalReadinessRead]:
    goals = session.exec(
        select(StrategicGoal)
        .where(StrategicGoal.status == "active")
        .order_by(col(StrategicGoal.created_at))
    ).all()
    targets = {target.id: target for target in session.exec(select(Target)).all()}
    links = session.exec(select(TargetGoalLink)).all()
    target_ids_by_goal: dict[UUID, list[UUID]] = {}
    for link in links:
        if link.target_id in targets:
            target_ids_by_goal.setdefault(link.goal_id, []).append(link.target_id)
    result: list[GoalReadinessRead] = []
    for goal in goals:
        target_ids = target_ids_by_goal.get(goal.id, [])
        direct_assessments = session.exec(
            select(StrategicGoalAssessment)
            .where(StrategicGoalAssessment.goal_id == goal.id)
            .order_by(col(StrategicGoalAssessment.version), col(StrategicGoalAssessment.created_at))
        ).all()
        if direct_assessments:
            latest = direct_assessments[-1]
            direct_trajectory = [
                GoalTrajectoryPoint(
                    created_at=item.created_at,
                    readiness_score=item.readiness_score,
                    overall_confidence=item.overall_confidence,
                    assessed_target_count=1,
                )
                for item in direct_assessments
            ]
            asset_ids = [UUID(value) for value in json.loads(latest.asset_ids_json)]
            assets = {
                asset.id: asset.title
                for asset in session.exec(
                    select(CareerAsset).where(col(CareerAsset.id).in_(asset_ids))
                ).all()
            } if asset_ids else {}
            trend = (
                round(
                    direct_trajectory[-1].readiness_score
                    - direct_trajectory[-2].readiness_score,
                    1,
                )
                if len(direct_trajectory) > 1 else None
            )
            score = latest.readiness_score
            readiness_status = (
                "on_track" if score >= 75
                else "progressing" if score >= 50
                else "needs_attention"
            )
            result.append(
                GoalReadinessRead(
                    goal_id=goal.id,
                    title=goal.title,
                    horizon=goal.horizon,
                    target_date=goal.target_date,
                    linked_target_ids=target_ids,
                    linked_target_titles=[targets[target_id].title for target_id in target_ids],
                    assessed_target_count=1,
                    readiness_score=score,
                    overall_confidence=latest.overall_confidence,
                    trend=trend,
                    status=readiness_status,
                    trajectory=direct_trajectory,
                    mapped_asset_ids=asset_ids,
                    mapped_asset_titles=[
                        assets[asset_id] for asset_id in asset_ids if asset_id in assets
                    ],
                    strengths=json.loads(latest.strengths_json),
                    gaps=json.loads(latest.gaps_json),
                    recommendations=json.loads(latest.recommendations_json),
                    explanation=latest.explanation,
                )
            )
            continue
        assessments = session.exec(
            select(ReadinessAssessment)
            .where(col(ReadinessAssessment.target_id).in_(target_ids))
            .order_by(col(ReadinessAssessment.created_at), col(ReadinessAssessment.version))
        ).all() if target_ids else []
        latest_by_target: dict[UUID, ReadinessAssessment] = {}
        trajectory: list[GoalTrajectoryPoint] = []
        for assessment in assessments:
            latest_by_target[assessment.target_id] = assessment
            current = list(latest_by_target.values())
            trajectory.append(
                GoalTrajectoryPoint(
                    created_at=assessment.created_at,
                    readiness_score=round(
                        sum(item.readiness_score for item in current) / len(current), 1
                    ),
                    overall_confidence=round(
                        sum(item.overall_confidence for item in current) / len(current), 1
                    ),
                    assessed_target_count=len(current),
                )
            )
        readiness_score = trajectory[-1].readiness_score if trajectory else None
        confidence = trajectory[-1].overall_confidence if trajectory else None
        trend = (
            round(trajectory[-1].readiness_score - trajectory[-2].readiness_score, 1)
            if len(trajectory) > 1 else None
        )
        if not target_ids:
            readiness_status = "not_mapped"
        elif not trajectory:
            readiness_status = "not_assessed"
        elif len(latest_by_target) < len(target_ids):
            readiness_status = "partially_assessed"
        elif readiness_score is not None and readiness_score >= 75:
            readiness_status = "on_track"
        elif readiness_score is not None and readiness_score >= 50:
            readiness_status = "progressing"
        else:
            readiness_status = "needs_attention"
        result.append(
            GoalReadinessRead(
                goal_id=goal.id,
                title=goal.title,
                horizon=goal.horizon,
                target_date=goal.target_date,
                linked_target_ids=target_ids,
                linked_target_titles=[targets[target_id].title for target_id in target_ids],
                assessed_target_count=len(latest_by_target),
                readiness_score=readiness_score,
                overall_confidence=confidence,
                trend=trend,
                status=readiness_status,
                trajectory=trajectory,
            )
        )
    return result


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
    for asset_link in session.exec(
        select(CriterionAssetLink).where(CriterionAssetLink.criterion_id == criterion.id)
    ).all():
        session.delete(asset_link)
    for evidence_link in session.exec(
        select(CriterionEvidenceLink).where(CriterionEvidenceLink.criterion_id == criterion.id)
    ).all():
        session.delete(evidence_link)
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
