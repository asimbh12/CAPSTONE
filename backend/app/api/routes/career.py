from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.db.session import get_session
from app.models.career import (
    AiHandlingPolicy,
    AssetStatus,
    CareerAsset,
    CareerProfile,
    Document,
    EvidenceItem,
    Organisation,
    Person,
    StrategicGoal,
    Theme,
)
from app.schemas.career import (
    AssetCreate,
    AssetList,
    AssetRead,
    AssetUpdate,
    DocumentRead,
    EvidenceCreate,
    EvidenceRead,
    GoalCreate,
    GoalRead,
    OrganisationCreate,
    OrganisationRead,
    PersonCreate,
    PersonRead,
    ProfileInput,
    ProfileRead,
    ThemeCreate,
    ThemeRead,
    TimelineItem,
)
from app.services.audit import record_audit
from app.services.career import (
    build_asset_read,
    create_asset,
    get_asset_or_404,
    query_assets,
    update_asset,
)
from app.services.documents import resolve_original_path, store_document

router = APIRouter()
SessionDependency = Annotated[Session, Depends(get_session)]


@router.get("/profile", response_model=ProfileRead | None)
def get_profile(session: SessionDependency) -> CareerProfile | None:
    return session.exec(select(CareerProfile).limit(1)).first()


@router.put("/profile", response_model=ProfileRead)
def put_profile(payload: ProfileInput, session: SessionDependency) -> CareerProfile:
    profile = session.exec(select(CareerProfile).limit(1)).first()
    action = "updated"
    if profile is None:
        profile = CareerProfile()
        action = "created"
    for key, value in payload.model_dump().items():
        setattr(profile, key, value)
    profile.updated_at = datetime.now(UTC)
    session.add(profile)
    session.flush()
    record_audit(session, entity_type="career_profile", entity_id=profile.id, action=action)
    session.commit()
    session.refresh(profile)
    return profile


@router.get("/themes", response_model=list[ThemeRead])
def list_themes(session: SessionDependency) -> list[Theme]:
    return list(session.exec(select(Theme).order_by(col(Theme.name))).all())


@router.post("/themes", response_model=ThemeRead, status_code=status.HTTP_201_CREATED)
def post_theme(payload: ThemeCreate, session: SessionDependency) -> Theme:
    theme = Theme(**payload.model_dump())
    session.add(theme)
    record_audit(session, entity_type="theme", entity_id=theme.id, action="created")
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=409, detail="A theme with this name already exists"
        ) from exc
    session.refresh(theme)
    return theme


@router.get("/goals", response_model=list[GoalRead])
def list_goals(session: SessionDependency) -> list[StrategicGoal]:
    return list(
        session.exec(select(StrategicGoal).order_by(col(StrategicGoal.created_at).desc())).all()
    )


@router.post("/goals", response_model=GoalRead, status_code=status.HTTP_201_CREATED)
def post_goal(payload: GoalCreate, session: SessionDependency) -> StrategicGoal:
    goal = StrategicGoal(**payload.model_dump())
    session.add(goal)
    record_audit(session, entity_type="strategic_goal", entity_id=goal.id, action="created")
    session.commit()
    session.refresh(goal)
    return goal


@router.get("/organisations", response_model=list[OrganisationRead])
def list_organisations(session: SessionDependency) -> list[Organisation]:
    return list(session.exec(select(Organisation).order_by(col(Organisation.name))).all())


@router.post("/organisations", response_model=OrganisationRead, status_code=status.HTTP_201_CREATED)
def post_organisation(payload: OrganisationCreate, session: SessionDependency) -> Organisation:
    organisation = Organisation(**payload.model_dump())
    session.add(organisation)
    record_audit(session, entity_type="organisation", entity_id=organisation.id, action="created")
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail="This organisation already exists") from exc
    session.refresh(organisation)
    return organisation


@router.get("/people", response_model=list[PersonRead])
def list_people(session: SessionDependency) -> list[Person]:
    return list(session.exec(select(Person).order_by(col(Person.name))).all())


@router.post("/people", response_model=PersonRead, status_code=status.HTTP_201_CREATED)
def post_person(payload: PersonCreate, session: SessionDependency) -> Person:
    if payload.organisation_id and session.get(Organisation, payload.organisation_id) is None:
        raise HTTPException(status_code=422, detail="Organisation does not exist")
    person = Person(**payload.model_dump())
    session.add(person)
    record_audit(session, entity_type="person", entity_id=person.id, action="created")
    session.commit()
    session.refresh(person)
    return person


@router.get("/assets", response_model=AssetList)
def list_assets(
    session: SessionDependency,
    search: str | None = Query(default=None, max_length=200),
    category: str | None = Query(default=None, max_length=100),
    asset_status: AssetStatus | None = None,
    theme_id: UUID | None = None,
) -> AssetList:
    records, total = query_assets(
        session,
        search=search,
        category=category,
        status_value=asset_status.value if asset_status else None,
        theme_id=theme_id,
    )
    return AssetList(items=[build_asset_read(session, item) for item in records], total=total)


@router.post("/assets", response_model=AssetRead, status_code=status.HTTP_201_CREATED)
def post_asset(payload: AssetCreate, session: SessionDependency) -> AssetRead:
    if payload.organisation_id and session.get(Organisation, payload.organisation_id) is None:
        raise HTTPException(status_code=422, detail="Organisation does not exist")
    asset = create_asset(session, payload)
    session.commit()
    session.refresh(asset)
    return build_asset_read(session, asset)


@router.get("/assets/{asset_id}", response_model=AssetRead)
def get_asset(asset_id: UUID, session: SessionDependency) -> AssetRead:
    return build_asset_read(session, get_asset_or_404(session, asset_id))


@router.put("/assets/{asset_id}", response_model=AssetRead)
def put_asset(asset_id: UUID, payload: AssetUpdate, session: SessionDependency) -> AssetRead:
    asset = get_asset_or_404(session, asset_id)
    if payload.organisation_id and session.get(Organisation, payload.organisation_id) is None:
        raise HTTPException(status_code=422, detail="Organisation does not exist")
    update_asset(session, asset, payload)
    session.commit()
    session.refresh(asset)
    return build_asset_read(session, asset)


@router.post("/assets/{asset_id}/archive", response_model=AssetRead)
def archive_asset(asset_id: UUID, session: SessionDependency) -> AssetRead:
    asset = get_asset_or_404(session, asset_id)
    asset.status = AssetStatus.ARCHIVED.value
    asset.archived_at = datetime.now(UTC)
    asset.updated_at = datetime.now(UTC)
    session.add(asset)
    record_audit(session, entity_type="career_asset", entity_id=asset.id, action="archived")
    session.commit()
    session.refresh(asset)
    return build_asset_read(session, asset)


@router.post(
    "/assets/{asset_id}/evidence",
    response_model=EvidenceRead,
    status_code=status.HTTP_201_CREATED,
)
def post_evidence(
    asset_id: UUID, payload: EvidenceCreate, session: SessionDependency
) -> EvidenceRead:
    get_asset_or_404(session, asset_id)
    if payload.document_id and session.get(Document, payload.document_id) is None:
        raise HTTPException(status_code=422, detail="Document does not exist")
    evidence = EvidenceItem(asset_id=asset_id, **payload.model_dump())
    session.add(evidence)
    session.flush()
    record_audit(session, entity_type="evidence_item", entity_id=evidence.id, action="created")
    session.commit()
    session.refresh(evidence)
    document = session.get(Document, evidence.document_id) if evidence.document_id else None
    return EvidenceRead(
        **evidence.model_dump(),
        document=DocumentRead.model_validate(document) if document else None,
    )


@router.post("/documents", response_model=DocumentRead)
async def upload_document(
    session: SessionDependency,
    file: Annotated[UploadFile, File()],
    ai_handling_policy: Annotated[AiHandlingPolicy, Form()] = AiHandlingPolicy.LOCAL_ONLY,
    confirmed_public_information: Annotated[bool, Form()] = False,
) -> Document:
    document, _ = await store_document(
        session,
        upload=file,
        policy=ai_handling_policy,
        confirmed_public_information=confirmed_public_information,
    )
    session.commit()
    session.refresh(document)
    return document


@router.get("/documents/{document_id}/download")
def download_document(document_id: UUID, session: SessionDependency) -> FileResponse:
    document = session.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return FileResponse(
        resolve_original_path(document),
        media_type=document.mime_type,
        filename=document.original_filename,
    )


@router.get("/timeline", response_model=list[TimelineItem])
def get_timeline(session: SessionDependency) -> list[TimelineItem]:
    assets = session.exec(
        select(CareerAsset)
        .where(CareerAsset.status != AssetStatus.ARCHIVED.value)
        .order_by(col(CareerAsset.start_date), col(CareerAsset.created_at))
    ).all()
    items: list[TimelineItem] = []
    for asset in assets:
        organisation = (
            session.get(Organisation, asset.organisation_id) if asset.organisation_id else None
        )
        items.append(
            TimelineItem(
                id=asset.id,
                title=asset.title,
                category=asset.category,
                start_date=asset.start_date,
                end_date=asset.end_date,
                role=asset.role,
                organisation=organisation.name if organisation else None,
            )
        )
    return items
