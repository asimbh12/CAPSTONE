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
    Provenance,
    StrategicGoal,
    Target,
    TargetCriterion,
)
from app.schemas.targets import (
    CriterionInput,
    CriterionMappingInput,
    CriterionRead,
    ProviderTargetSuggestionResponse,
    ReadinessInput,
    ReadinessRead,
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
    readiness_read,
    replace_mappings,
    target_read,
)

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]


@router.get("", response_model=list[TargetRead])
def list_targets(session: SessionDependency) -> list[TargetRead]:
    targets = session.exec(select(Target).order_by(col(Target.updated_at).desc())).all()
    return [target_read(session, target) for target in targets if target.status != "archived"]


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
