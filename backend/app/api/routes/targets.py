import json
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, col, select

from app.core.config import get_settings
from app.db.session import get_session
from app.models.career import (
    AiOperation,
    CareerAsset,
    CareerProfile,
    EvidenceItem,
    Provenance,
    StrategicGoal,
    StrategicGoalAssessment,
    Target,
    TargetCriterion,
)
from app.schemas.targets import (
    CriterionAssessmentInput,
    CriterionInput,
    CriterionMappingInput,
    CriterionRead,
    GoalReadinessRead,
    ProviderGoalAssessment,
    ProviderTargetMappingResponse,
    ProviderTargetSuggestionResponse,
    ReadinessInput,
    ReadinessRead,
    TargetGoalMappingInput,
    TargetInput,
    TargetRead,
    TargetSuggestionResponse,
)
from app.services.audit import record_audit
from app.services.targets import (
    assess_target,
    criterion_read,
    get_criterion_or_404,
    get_target_or_404,
    goal_readiness,
    readiness_read,
    replace_mappings,
    replace_target_goals,
    target_read,
)

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]


@router.get("", response_model=list[TargetRead])
def list_targets(session: SessionDependency) -> list[TargetRead]:
    targets = session.exec(select(Target).order_by(col(Target.updated_at).desc())).all()
    return [target_read(session, target) for target in targets if target.status != "archived"]


@router.get("/goal-readiness", response_model=list[GoalReadinessRead])
def list_goal_readiness(session: SessionDependency) -> list[GoalReadinessRead]:
    return goal_readiness(session)


@router.post("/goals/{goal_id}/auto-assess", response_model=GoalReadinessRead)
def auto_assess_goal(goal_id: UUID, session: SessionDependency) -> GoalReadinessRead:
    settings = get_settings()
    if settings.ai_provider.lower() != "gemini" or not settings.gemini_api_key:
        raise HTTPException(status_code=409, detail="Gemini is not configured for goal assessment")
    goal = session.get(StrategicGoal, goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail="Strategic goal not found")
    assets = session.exec(
        select(CareerAsset).where(CareerAsset.status != "archived").limit(400)
    ).all()
    if not assets:
        raise HTTPException(status_code=422, detail="No active career achievements are available")
    evidence_by_asset: dict[UUID, list[EvidenceItem]] = {}
    for evidence in session.exec(select(EvidenceItem)).all():
        evidence_by_asset.setdefault(evidence.asset_id, []).append(evidence)
    asset_context = [
        {
            "id": str(asset.id),
            "title": asset.title,
            "category": asset.category,
            "description": asset.description,
            "impact_summary": asset.impact_summary,
            "role": asset.role,
            "start_date": str(asset.start_date or ""),
            "evidence": [
                {"id": str(item.id), "title": item.title, "description": item.description}
                for item in evidence_by_asset.get(asset.id, [])
            ],
        }
        for asset in assets
    ]
    from google import genai

    client = genai.Client(api_key=settings.gemini_api_key)
    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=(
                "Assess current readiness for the supplied strategic career goal using only the "
                "supplied public career achievements and evidence. Map every genuinely relevant "
                "achievement by its supplied ID. Readiness is demonstrated progress toward the "
                "goal from 0-100, not the probability of future success. Do not claim the goal "
                "itself is achieved unless evidence explicitly proves it. Identify established "
                "strengths, genuine gaps, and specific next actions. Confidence reflects evidence "
                "quality.\n\n"
                f"GOAL: {goal.model_dump(mode='json')}\nACHIEVEMENTS: {asset_context}"
            ),
            config={
                "response_mime_type": "application/json",
                "response_schema": ProviderGoalAssessment,
                "temperature": 0.1,
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Gemini could not complete the goal assessment: {exc}",
        ) from exc
    provider_result = ProviderGoalAssessment.model_validate_json(response.text or "{}")
    assets_by_id = {str(asset.id): asset for asset in assets}
    mapped_assets = list(
        dict.fromkeys(
            assets_by_id[asset_id].id
            for asset_id in provider_result.asset_ids
            if asset_id in assets_by_id
        )
    )
    evidence_ids = list(
        dict.fromkeys(
            evidence.id
            for asset_id in mapped_assets
            for evidence in evidence_by_asset.get(asset_id, [])
        )
    )
    previous = session.exec(
        select(StrategicGoalAssessment)
        .where(StrategicGoalAssessment.goal_id == goal.id)
        .order_by(col(StrategicGoalAssessment.version).desc())
    ).first()
    assessment = StrategicGoalAssessment(
        goal_id=goal.id,
        version=previous.version + 1 if previous else 1,
        provider="gemini",
        model=settings.gemini_model,
        readiness_score=round(provider_result.readiness_score, 1),
        overall_confidence=round(provider_result.confidence, 1),
        explanation=provider_result.explanation,
        strengths_json=json.dumps(provider_result.strengths),
        gaps_json=json.dumps(provider_result.gaps),
        recommendations_json=json.dumps(provider_result.recommendations),
        asset_ids_json=json.dumps([str(value) for value in mapped_assets]),
        evidence_ids_json=json.dumps([str(value) for value in evidence_ids]),
    )
    session.add(assessment)
    session.flush()
    record_audit(
        session,
        entity_type="strategic_goal_assessment",
        entity_id=assessment.id,
        action="ai_evidence_mapped",
        source=Provenance.AI.value,
        details={
            "goal_id": str(goal.id),
            "assets": len(mapped_assets),
            "version": assessment.version,
        },
    )
    session.add(
        AiOperation(
            operation="assess_strategic_goal",
            entity_type="strategic_goal",
            entity_id=str(goal.id),
            provider="gemini",
            model=settings.gemini_model,
            status="completed",
            input_characters=len(str(asset_context)),
            output_characters=len(response.text or ""),
        )
    )
    session.commit()
    return next(item for item in goal_readiness(session) if item.goal_id == goal.id)


@router.post("", response_model=TargetRead, status_code=status.HTTP_201_CREATED)
def create_target(payload: TargetInput, session: SessionDependency) -> TargetRead:
    target = Target(**payload.model_dump(exclude={"criteria"}))
    session.add(target)
    session.flush()
    for index, criterion in enumerate(payload.criteria):
        data = criterion.model_dump()
        if not data["sort_order"]:
            data["sort_order"] = index
        session.add(TargetCriterion(target_id=target.id, **data))
    record_audit(
        session,
        entity_type="target",
        entity_id=target.id,
        action="created" if target.status == "adopted" else "suggestion_adopted",
        source=target.provenance,
    )
    session.commit()
    session.refresh(target)
    return target_read(session, target)


@router.put("/{target_id}", response_model=TargetRead)
def update_target(target_id: UUID, payload: TargetInput, session: SessionDependency) -> TargetRead:
    target = get_target_or_404(session, target_id)
    for key, value in payload.model_dump(exclude={"criteria", "provenance"}).items():
        setattr(target, key, value)
    target.updated_at = datetime.now(UTC)
    session.add(target)
    record_audit(session, entity_type="target", entity_id=target.id, action="updated")
    session.commit()
    session.refresh(target)
    return target_read(session, target)


@router.put("/{target_id}/goals", response_model=TargetRead)
def map_target_goals(
    target_id: UUID, payload: TargetGoalMappingInput, session: SessionDependency
) -> TargetRead:
    target = get_target_or_404(session, target_id)
    replace_target_goals(session, target, payload.goal_ids)
    record_audit(
        session,
        entity_type="target",
        entity_id=target.id,
        action="strategic_goals_mapped",
        details={"goal_ids": payload.goal_ids},
    )
    session.commit()
    return target_read(session, target)


@router.post("/{target_id}/criteria", response_model=CriterionRead)
def add_criterion(
    target_id: UUID, payload: CriterionInput, session: SessionDependency
) -> CriterionRead:
    get_target_or_404(session, target_id)
    criterion = TargetCriterion(target_id=target_id, **payload.model_dump())
    session.add(criterion)
    session.flush()
    record_audit(session, entity_type="target_criterion", entity_id=criterion.id, action="created")
    session.commit()
    session.refresh(criterion)
    return criterion_read(session, criterion)


@router.put("/criteria/{criterion_id}", response_model=CriterionRead)
def update_criterion(
    criterion_id: UUID, payload: CriterionInput, session: SessionDependency
) -> CriterionRead:
    criterion = get_criterion_or_404(session, criterion_id)
    for key, value in payload.model_dump(exclude={"provenance"}).items():
        setattr(criterion, key, value)
    criterion.updated_at = datetime.now(UTC)
    session.add(criterion)
    record_audit(session, entity_type="target_criterion", entity_id=criterion.id, action="updated")
    session.commit()
    session.refresh(criterion)
    return criterion_read(session, criterion)


@router.put("/criteria/{criterion_id}/mappings", response_model=CriterionRead)
def map_criterion(
    criterion_id: UUID, payload: CriterionMappingInput, session: SessionDependency
) -> CriterionRead:
    criterion = get_criterion_or_404(session, criterion_id)
    replace_mappings(session, criterion, payload.asset_ids, payload.evidence_ids)
    record_audit(
        session,
        entity_type="target_criterion",
        entity_id=criterion.id,
        action="evidence_mapped",
        details={"assets": len(payload.asset_ids), "evidence": len(payload.evidence_ids)},
    )
    session.commit()
    return criterion_read(session, criterion)


@router.post("/{target_id}/assessments", response_model=ReadinessRead)
def create_assessment(
    target_id: UUID, payload: ReadinessInput, session: SessionDependency
) -> ReadinessRead:
    target = get_target_or_404(session, target_id)
    if target.status != "adopted":
        raise HTTPException(status_code=409, detail="Adopt the target before assessing readiness")
    assessment = assess_target(session, target, payload)
    record_audit(
        session,
        entity_type="readiness_assessment",
        entity_id=assessment.id,
        action="created",
        source=Provenance.RULE.value,
        details={"target_id": str(target.id), "version": assessment.version},
    )
    session.commit()
    session.refresh(assessment)
    return readiness_read(session, assessment)


@router.post("/{target_id}/auto-map", response_model=ReadinessRead)
def auto_map_target(target_id: UUID, session: SessionDependency) -> ReadinessRead:
    """Semantically map active assets to target criteria and create a readiness version."""
    settings = get_settings()
    if settings.ai_provider.lower() != "gemini" or not settings.gemini_api_key:
        raise HTTPException(status_code=409, detail="Gemini is not configured for evidence mapping")
    target = get_target_or_404(session, target_id)
    if target.status != "adopted":
        raise HTTPException(status_code=409, detail="Adopt the target before mapping evidence")
    criteria = session.exec(
        select(TargetCriterion)
        .where(TargetCriterion.target_id == target.id)
        .order_by(col(TargetCriterion.sort_order), col(TargetCriterion.created_at))
    ).all()
    assets = session.exec(
        select(CareerAsset)
        .where(CareerAsset.status != "archived")
        .order_by(col(CareerAsset.updated_at).desc())
        .limit(300)
    ).all()
    if not criteria:
        raise HTTPException(status_code=422, detail="The target has no readiness criteria")
    if not assets:
        raise HTTPException(status_code=422, detail="No active career assets are available to map")

    evidence_by_asset: dict[UUID, list[EvidenceItem]] = {}
    for evidence in session.exec(select(EvidenceItem)).all():
        evidence_by_asset.setdefault(evidence.asset_id, []).append(evidence)

    asset_context = [
        {
            "id": str(asset.id),
            "title": asset.title,
            "category": asset.category,
            "description": asset.description,
            "impact_summary": asset.impact_summary,
            "role": asset.role,
            "tags": json.loads(asset.tags_json),
            "keywords": json.loads(asset.keywords_json),
            "evidence": [
                {
                    "id": str(evidence.id),
                    "title": evidence.title,
                    "description": evidence.description,
                    "source_url": evidence.source_url,
                }
                for evidence in evidence_by_asset.get(asset.id, [])
            ],
        }
        for asset in assets
    ]
    criterion_context = [
        {"id": str(item.id), "title": item.title, "description": item.description}
        for item in criteria
    ]
    from google import genai

    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=(
            "Map the supplied public career assets to every target criterion. Use only asset IDs "
            "from the supplied list. Match semantically, including equivalent roles, "
            "achievements, scale and impact; do not rely only on exact title words. Multiple "
            "assets may support a criterion and one asset may support several criteria. Coverage "
            "is demonstrated current readiness from 0-100, not whether the future target itself "
            "is already achieved. Confidence reflects evidence quality from 0-100. Do not treat "
            "an aspiration or missing award as an achievement. Explain the factual basis and give "
            "a specific action only for a genuine gap. "
            "Return exactly one result for every criterion ID.\n\n"
            f"TARGET: {target.title}\nCRITERIA: {criterion_context}\nACTIVE ASSETS: {asset_context}"
        ),
        config={
            "response_mime_type": "application/json",
            "response_schema": ProviderTargetMappingResponse,
            "temperature": 0.1,
        },
    )
    provider_result = ProviderTargetMappingResponse.model_validate_json(response.text or "{}")
    asset_by_id = {str(asset.id): asset for asset in assets}
    result_by_criterion = {item.criterion_id: item for item in provider_result.criteria}
    assessment_inputs: list[CriterionAssessmentInput] = []
    for criterion in criteria:
        mapped = result_by_criterion.get(str(criterion.id))
        existing = criterion_read(session, criterion)
        ai_assets = list(
            dict.fromkeys(
                asset_by_id[asset_id].id
                for asset_id in (mapped.asset_ids if mapped else [])
                if asset_id in asset_by_id
            )
        )
        valid_assets = list(dict.fromkeys([*existing.asset_ids, *ai_assets]))
        ai_evidence_ids = list(
            dict.fromkeys(
                evidence.id
                for asset_id in ai_assets
                for evidence in evidence_by_asset.get(asset_id, [])
            )
        )
        evidence_ids = list(dict.fromkeys([*existing.evidence_ids, *ai_evidence_ids]))
        replace_mappings(session, criterion, valid_assets, evidence_ids)
        assessment_inputs.append(
            CriterionAssessmentInput(
                criterion_id=criterion.id,
                coverage=max(0, min(float(mapped.coverage), 100)) if mapped else 0,
                confidence=max(0, min(float(mapped.confidence), 100)) if mapped else 0,
                explanation=mapped.explanation if mapped else "AI returned no assessment.",
                recommended_action=mapped.recommended_action
                if mapped
                else "Review this criterion manually.",
            )
        )
    assessment = assess_target(session, target, ReadinessInput(criteria=assessment_inputs))
    record_audit(
        session,
        entity_type="readiness_assessment",
        entity_id=assessment.id,
        action="ai_evidence_mapped",
        source=Provenance.AI.value,
        details={"target_id": str(target.id), "version": assessment.version},
    )
    session.add(
        AiOperation(
            operation="map_target_evidence",
            entity_type="target",
            entity_id=str(target.id),
            provider="gemini",
            model=settings.gemini_model,
            status="completed",
            input_characters=len(str(asset_context)) + len(str(criterion_context)),
            output_characters=len(response.text or ""),
        )
    )
    session.commit()
    session.refresh(assessment)
    return readiness_read(session, assessment)


@router.post("/suggestions", response_model=TargetSuggestionResponse)
def suggest_targets(session: SessionDependency) -> TargetSuggestionResponse:
    settings = get_settings()
    if settings.ai_provider.lower() != "gemini" or not settings.gemini_api_key:
        raise HTTPException(
            status_code=409, detail="Gemini is not configured for target suggestions"
        )
    profile = session.exec(select(CareerProfile).limit(1)).first()
    goals = session.exec(select(StrategicGoal).limit(20)).all()
    assets = session.exec(select(CareerAsset).limit(100)).all()
    context = {
        "profile": profile.model_dump(mode="json") if profile else {},
        "goals": [item.model_dump(mode="json") for item in goals],
        "career_assets": [
            {"title": item.title, "category": item.category, "impact": item.impact_summary}
            for item in assets
        ],
    }
    from google import genai

    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=(
            "Using only this public professional context, suggest up to three ambitious but "
            "plausible career targets or trajectories. For each, provide a rationale, milestones, "
            "and 3-8 measurable weighted readiness criteria. These are proposals only; do not "
            f"claim they are adopted.\n\n{context}"
        ),
        config={
            "response_mime_type": "application/json",
            "response_schema": ProviderTargetSuggestionResponse,
            "temperature": 0.2,
        },
    )
    provider_result = ProviderTargetSuggestionResponse.model_validate_json(response.text or "{}")
    suggestions = provider_result.model_dump()["suggestions"]
    for suggestion in suggestions:
        for index, criterion in enumerate(suggestion["criteria"]):
            criterion["provenance"] = "ai"
            criterion["weight"] = max(0.1, min(float(criterion["weight"] or 1), 100))
            criterion["sort_order"] = index
    result = TargetSuggestionResponse.model_validate(
        {"provider": "gemini", "suggestions": suggestions}
    )
    session.add(
        AiOperation(
            operation="suggest_career_targets",
            entity_type="target_suggestion",
            entity_id="unadopted",
            provider="gemini",
            model=settings.gemini_model,
            status="completed",
            input_characters=len(str(context)),
            output_characters=len(response.text or ""),
        )
    )
    session.commit()
    return result
