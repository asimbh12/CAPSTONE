import json
import re
from collections.abc import Sequence
from datetime import UTC, datetime
from difflib import SequenceMatcher
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
    TimelineDuplicateCandidate,
    TimelineDuplicateGroup,
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


_TITLE_FILLER_WORDS = {
    "a", "an", "and", "at", "for", "in", "of", "on", "the", "to", "with",
}


def _normalise_comparison_text(value: str) -> str:
    words = re.findall(r"[a-z0-9]+", value.casefold())
    return " ".join(word for word in words if word not in _TITLE_FILLER_WORDS)


def _title_similarity(left: str, right: str) -> float:
    left_normalised = _normalise_comparison_text(left)
    right_normalised = _normalise_comparison_text(right)
    if not left_normalised or not right_normalised:
        return 0
    sequence_score = SequenceMatcher(None, left_normalised, right_normalised).ratio()
    left_tokens = set(left_normalised.split())
    right_tokens = set(right_normalised.split())
    token_score = len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
    containment = len(left_tokens & right_tokens) / min(len(left_tokens), len(right_tokens))
    return max(sequence_score, token_score, containment * 0.92)


def find_timeline_duplicate_groups(session: Session) -> list[TimelineDuplicateGroup]:
    assets = list(
        session.exec(
            select(CareerAsset)
            .where(CareerAsset.status != "archived")
            .order_by(col(CareerAsset.created_at))
        ).all()
    )
    organisations = {
        organisation.id: organisation.name
        for organisation in session.exec(select(Organisation)).all()
    }
    evidence_counts = {
        asset.id: int(
            session.exec(
                select(func.count())
                .select_from(EvidenceItem)
                .where(EvidenceItem.asset_id == asset.id)
            ).one()
        )
        for asset in assets
    }
    links: list[tuple[int, int, int, list[str]]] = []
    for left_index, left in enumerate(assets):
        for right_index in range(left_index + 1, len(assets)):
            right = assets[right_index]
            title_score = _title_similarity(left.title, right.title)
            same_date = bool(left.start_date and left.start_date == right.start_date)
            same_year = bool(
                left.start_date
                and right.start_date
                and left.start_date.year == right.start_date.year
            )
            left_organisation = (
                organisations.get(left.organisation_id, "") if left.organisation_id else ""
            )
            right_organisation = (
                organisations.get(right.organisation_id, "") if right.organisation_id else ""
            )
            same_organisation = bool(
                left_organisation
                and _normalise_comparison_text(left_organisation)
                == _normalise_comparison_text(right_organisation)
            )
            same_category = bool(
                left.category
                and _normalise_comparison_text(left.category)
                == _normalise_comparison_text(right.category)
            )
            same_role = bool(
                left.role
                and right.role
                and _title_similarity(left.role, right.role) >= 0.85
            )
            contextual_matches = sum((same_date, same_organisation, same_category, same_role))
            is_candidate = title_score >= 0.8 or (
                title_score >= 0.68 and (same_date or (same_year and contextual_matches >= 1))
            )
            if not is_candidate:
                continue
            confidence = round(
                min(
                    99,
                    title_score * 72
                    + (12 if same_date else 5 if same_year else 0)
                    + (6 if same_organisation else 0)
                    + (5 if same_category else 0)
                    + (5 if same_role else 0),
                )
            )
            reasons = [f"Similar title wording ({round(title_score * 100)}%)"]
            if same_date:
                reasons.append("Same start date")
            elif same_year:
                reasons.append("Same start year")
            if same_organisation:
                reasons.append("Same organisation")
            if same_category:
                reasons.append("Same category")
            if same_role:
                reasons.append("Similar role")
            links.append((left_index, right_index, confidence, reasons))

    parent = list(range(len(assets)))

    def root(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for left_index, right_index, _, _ in links:
        left_root, right_root = root(left_index), root(right_index)
        if left_root != right_root:
            parent[right_root] = left_root

    grouped_indexes: dict[int, set[int]] = {}
    for left_index, right_index, _, _ in links:
        group = grouped_indexes.setdefault(root(left_index), set())
        group.update((left_index, right_index))

    groups: list[TimelineDuplicateGroup] = []
    for indexes in grouped_indexes.values():
        relevant_links = [link for link in links if link[0] in indexes and link[1] in indexes]
        reasons = list(dict.fromkeys(reason for link in relevant_links for reason in link[3]))
        candidates: list[TimelineDuplicateCandidate] = []
        for index in sorted(indexes):
            asset = assets[index]
            candidates.append(
                TimelineDuplicateCandidate(
                    id=asset.id,
                    title=asset.title,
                    description=asset.description,
                    category=asset.category,
                    start_date=asset.start_date,
                    end_date=asset.end_date,
                    role=asset.role,
                    organisation=(
                        organisations.get(asset.organisation_id) if asset.organisation_id else None
                    ),
                    source_kind=asset.source_kind,
                    evidence_count=evidence_counts[asset.id],
                )
            )
        groups.append(
            TimelineDuplicateGroup(
                confidence=max(link[2] for link in relevant_links),
                reasons=reasons,
                items=candidates,
            )
        )
    return sorted(groups, key=lambda group: group.confidence, reverse=True)
