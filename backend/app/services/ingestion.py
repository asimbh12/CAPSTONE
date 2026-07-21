import ipaddress
import json
import re
import socket
from datetime import UTC, datetime
from html import unescape
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models.career import (
    AiHandlingPolicy,
    AssetThemeLink,
    CareerAsset,
    CareerProfile,
    EvidenceItem,
    IngestionRun,
    Organisation,
    Provenance,
    Theme,
)
from app.schemas.ingestion import ApplyIngestionResult, CareerExtractionProposal
from app.services.ai import get_career_extractor
from app.services.audit import record_audit


def ingestion_read(run: IngestionRun) -> dict[str, object]:
    return {**run.model_dump(exclude={"proposal_json"}), "proposal": json.loads(run.proposal_json)}


def create_ingestion(
    session: Session,
    *,
    source_type: str,
    source_label: str,
    text: str,
    policy: AiHandlingPolicy,
    document_id: UUID | None = None,
    source_url: str = "",
) -> IngestionRun:
    if not text.strip():
        raise HTTPException(status_code=422, detail="No readable text was found in this source")
    extractor = get_career_extractor(policy)
    try:
        proposal = extractor.extract(text, source_label)
        run = IngestionRun(
            source_type=source_type,
            source_label=source_label,
            source_url=source_url,
            document_id=document_id,
            ai_handling_policy=policy.value,
            provider=extractor.name,
            proposal_json=proposal.model_dump_json(),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"Career extraction failed: {str(exc)[:500]}"
        ) from exc
    session.add(run)
    session.flush()
    record_audit(
        session,
        entity_type="ingestion_run",
        entity_id=run.id,
        action="proposed",
        source=Provenance.AI.value if extractor.name == "gemini" else Provenance.RULE.value,
        details={"source_type": source_type, "provider": extractor.name},
    )
    return run


def fetch_public_page(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(status_code=422, detail="Enter a valid public HTTP or HTTPS URL")
    try:
        addresses = socket.getaddrinfo(
            parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80)
        )
        if any(
            ipaddress.ip_address(item[4][0]).is_private
            or ipaddress.ip_address(item[4][0]).is_loopback
            or ipaddress.ip_address(item[4][0]).is_reserved
            for item in addresses
        ):
            raise HTTPException(
                status_code=422, detail="Local and private network URLs are not allowed"
            )
        request = Request(url, headers={"User-Agent": "CAPSTONE/0.1 career-source-reader"})
        with urlopen(request, timeout=12) as response:  # noqa: S310 - host is validated above
            content_type = response.headers.get_content_type()
            if content_type not in {"text/html", "text/plain"}:
                raise HTTPException(
                    status_code=415, detail="The URL must return an HTML or text page"
                )
            raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                raise HTTPException(status_code=413, detail="Public page is larger than 2 MB")
            charset = response.headers.get_content_charset() or "utf-8"
        html = raw.decode(charset, errors="replace")
    except HTTPException:
        raise
    except (OSError, UnicodeError) as exc:
        raise HTTPException(
            status_code=422, detail=f"Unable to read the public URL: {exc}"
        ) from exc
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    label = unescape(re.sub(r"\s+", " ", title_match.group(1)).strip()) if title_match else url
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.I | re.S)
    text = unescape(re.sub(r"<[^>]+>", "\n", text))
    return label[:500], re.sub(r"\n\s*\n+", "\n", text).strip()


def apply_ingestion(
    session: Session, run: IngestionRun, proposal: CareerExtractionProposal
) -> ApplyIngestionResult:
    if run.status == "applied":
        raise HTTPException(status_code=409, detail="This ingestion has already been applied")
    profile = session.exec(select(CareerProfile).limit(1)).first()
    created_profile = profile is None
    if profile is None:
        profile = CareerProfile()
    filled: list[str] = []
    for field in ("name", "current_title", "current_organisation", "career_narrative"):
        proposed = getattr(proposal.profile, field)
        if proposed and not getattr(profile, field):
            setattr(profile, field, proposed)
            filled.append(field)
    profile.updated_at = datetime.now(UTC)
    session.add(profile)

    themes_created = 0
    themes: dict[str, Theme] = {
        item.name.casefold(): item for item in session.exec(select(Theme)).all()
    }
    for name in dict.fromkeys([*proposal.themes, *(x for a in proposal.assets for x in a.themes)]):
        clean = name.strip()[:100]
        if clean and clean.casefold() not in themes:
            theme = Theme(name=clean, provenance=Provenance.AI.value)
            session.add(theme)
            session.flush()
            themes[clean.casefold()] = theme
            themes_created += 1

    organisations_created = assets_created = assets_skipped = 0
    existing_titles = {title.casefold() for title in session.exec(select(CareerAsset.title)).all()}
    organisations = {
        item.name.casefold(): item for item in session.exec(select(Organisation)).all()
    }
    for item in proposal.assets:
        if not item.include or item.title.casefold() in existing_titles:
            assets_skipped += 1
            continue
        organisation = None
        if item.organisation.strip():
            key = item.organisation.strip().casefold()
            organisation = organisations.get(key)
            if organisation is None:
                organisation = Organisation(
                    name=item.organisation.strip()[:250], provenance=Provenance.EXTRACTED.value
                )
                session.add(organisation)
                session.flush()
                organisations[key] = organisation
                organisations_created += 1
        asset = CareerAsset(
            title=item.title,
            description=item.description,
            category=item.category or "Experience",
            role=item.role,
            organisation_id=organisation.id if organisation else None,
            start_date=item.start_date,
            end_date=item.end_date,
            impact_summary=item.impact_summary,
            tags_json=json.dumps(item.tags),
            keywords_json="[]",
            source_kind=Provenance.EXTRACTED.value,
        )
        session.add(asset)
        session.flush()
        existing_titles.add(item.title.casefold())
        assets_created += 1
        for name in item.themes:
            linked_theme = themes.get(name.strip().casefold())
            if linked_theme:
                session.add(
                    AssetThemeLink(
                        asset_id=asset.id,
                        theme_id=linked_theme.id,
                        provenance=Provenance.AI.value,
                    )
                )
        session.add(
            EvidenceItem(
                asset_id=asset.id,
                document_id=run.document_id,
                title=run.source_label[:250],
                description="Source used during reviewed career ingestion.",
                source_url=run.source_url,
                source_kind=Provenance.EXTRACTED.value,
            )
        )
    run.proposal_json = proposal.model_dump_json()
    run.status = "applied"
    run.applied_at = datetime.now(UTC)
    session.add(run)
    record_audit(
        session,
        entity_type="ingestion_run",
        entity_id=run.id,
        action="applied",
        source=Provenance.USER.value,
        details={"assets_created": assets_created, "profile_fields_filled": filled},
    )
    return ApplyIngestionResult(
        profile_created=created_profile,
        profile_fields_filled=filled,
        assets_created=assets_created,
        assets_skipped=assets_skipped,
        organisations_created=organisations_created,
        themes_created=themes_created,
    )
