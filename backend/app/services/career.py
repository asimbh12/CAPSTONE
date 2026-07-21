import json
from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import Session, col, func, or_, select

from app.models.career import (
    AssetThemeLink,
    CareerAsset,
    Document,
    EvidenceItem,
    Organisation,
    Theme,
)
from app.schemas.career import (
    AssetCreate,
    AssetRead,
    DocumentRead,
    EvidenceRead,
    OrganisationRead,
    ThemeRead,
)
from app.services.audit import record_audit


def _json_list(value: str) -> list[str]:
    parsed = json.loads(value)
    return [str(item) for item in parsed] if isinstance(parsed, list) else []


def _get_themes(session: Session, asset_id: UUID) -> list[Theme]:
    statement = (
        select(Theme)
        .join(AssetThemeLink, col(AssetThemeLink.theme_id) == col(Theme.id))
        .where(AssetThemeLink.asset_id == asset_id)
        .order_by(col(Theme.name))
    )
    return list(session.exec(statement).all())


def _get_evidence(session: Session, asset_id: UUID) -> list[EvidenceRead]:
    records = session.exec(
        select(EvidenceItem)
        .where(EvidenceItem.asset_id == asset_id)
        .order_by(col(EvidenceItem.created_at).desc())
    ).all()
    result: list[EvidenceRead] = []
    for record in records:
        document = session.get(Document, record.document_id) if record.document_id else None
        result.append(
            EvidenceRead(
                **record.model_dump(),
                document=DocumentRead.model_validate(document) if document else None,
            )
        )
    return result


def build_asset_read(session: Session, asset: CareerAsset) -> AssetRead:
    organisation = (
        session.get(Organisation, asset.organisation_id) if asset.organisation_id else None
    )
    themes = _get_themes(session, asset.id)
    return AssetRead(
        **asset.model_dump(exclude={"tags_json", "keywords_json"}),
        tags=_json_list(asset.tags_json),
        keywords=_json_list(asset.keywords_json),
        theme_ids=[theme.id for theme in themes],
        themes=[ThemeRead.model_validate(theme) for theme in themes],
        evidence=_get_evidence(session, asset.id),
        organisation=OrganisationRead.model_validate(organisation) if organisation else None,
    )


def get_asset_or_404(session: Session, asset_id: UUID) -> CareerAsset:
    asset = session.get(CareerAsset, asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Career asset not found")
    return asset


def sync_asset_themes(session: Session, asset_id: UUID, theme_ids: Sequence[UUID]) -> None:
    unique_ids = list(dict.fromkeys(theme_ids))
    if unique_ids:
        existing_themes = session.exec(select(Theme).where(col(Theme.id).in_(unique_ids))).all()
        if len(existing_themes) != len(unique_ids):
            raise HTTPException(status_code=422, detail="One or more theme IDs do not exist")
    existing_links = session.exec(
        select(AssetThemeLink).where(AssetThemeLink.asset_id == asset_id)
    ).all()
    existing_by_theme = {link.theme_id: link for link in existing_links}
    requested = set(unique_ids)
    for theme_id, link in existing_by_theme.items():
        if theme_id not in requested:
            session.delete(link)
    for theme_id in unique_ids:
        if theme_id not in existing_by_theme:
            session.add(AssetThemeLink(asset_id=asset_id, theme_id=theme_id))


def create_asset(session: Session, payload: AssetCreate, *, source: str = "user") -> CareerAsset:
    values = payload.model_dump(exclude={"tags", "keywords", "theme_ids"})
    asset = CareerAsset(
        **values,
        tags_json=json.dumps(payload.tags),
        keywords_json=json.dumps(payload.keywords),
        source_kind=source,
    )
    session.add(asset)
    session.flush()
    sync_asset_themes(session, asset.id, payload.theme_ids)
    record_audit(
        session, entity_type="career_asset", entity_id=asset.id, action="created", source=source
    )
    return asset


def update_asset(session: Session, asset: CareerAsset, payload: AssetCreate) -> CareerAsset:
    values = payload.model_dump(exclude={"tags", "keywords", "theme_ids"})
    for key, value in values.items():
        setattr(asset, key, value)
    asset.tags_json = json.dumps(payload.tags)
    asset.keywords_json = json.dumps(payload.keywords)
    asset.updated_at = datetime.now(UTC)
    session.add(asset)
    sync_asset_themes(session, asset.id, payload.theme_ids)
    record_audit(session, entity_type="career_asset", entity_id=asset.id, action="updated")
    return asset


def query_assets(
    session: Session,
    *,
    search: str | None,
    category: str | None,
    status_value: str | None,
    theme_id: UUID | None,
) -> tuple[list[CareerAsset], int]:
    statement = select(CareerAsset)
    count_statement = select(func.count()).select_from(CareerAsset)
    filters: list[ColumnElement[bool]] = []
    if search:
        pattern = f"%{search.strip()}%"
        filters.append(
            or_(
                col(CareerAsset.title).ilike(pattern),
                col(CareerAsset.description).ilike(pattern),
                col(CareerAsset.impact_summary).ilike(pattern),
                col(CareerAsset.tags_json).ilike(pattern),
            )
        )
    if category:
        filters.append(col(CareerAsset.category) == category)
    if status_value:
        filters.append(col(CareerAsset.status) == status_value)
    if theme_id:
        asset_ids = select(AssetThemeLink.asset_id).where(AssetThemeLink.theme_id == theme_id)
        filters.append(col(CareerAsset.id).in_(asset_ids))
    if filters:
        statement = statement.where(*filters)
        count_statement = count_statement.where(*filters)
    statement = statement.order_by(
        col(CareerAsset.start_date).desc(), col(CareerAsset.created_at).desc()
    )
    return list(session.exec(statement).all()), int(session.exec(count_statement).one())
