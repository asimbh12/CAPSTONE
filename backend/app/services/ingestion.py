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

from app.core.config import get_settings
from app.models.career import (
    AiHandlingPolicy,
    AiOperation,
    AssetThemeLink,
    CareerAsset,
    CareerProfile,
    Document,
    EvidenceItem,
    IngestionRun,
    Organisation,
    Provenance,
    Theme,
)
from app.schemas.ingestion import (
    ApplyIngestionResult,
    AssetEnrichmentResult,
    CareerExtractionProposal,
    ProposedAsset,
    PublicProfileSource,
)
from app.services.ai import get_career_extractor
from app.services.audit import record_audit

DEAKIN_PROFILE_SECTIONS = (
    ("profile", ""),
    ("research_outputs", "/publications"),
    ("research_grants", "/grants"),
    ("professional_activities", "/professional"),
    ("teaching_supervision", "/teaching"),
)


def expand_public_profile_sources(url: str) -> list[PublicProfileSource]:
    """Expand supported profile hubs into their public, first-party section pages."""
    parsed = urlparse(url)
    if parsed.hostname not in {"experts.deakin.edu.au", "www.experts.deakin.edu.au"}:
        return [PublicProfileSource(url=url, source_type="other")]
    segments = [segment for segment in parsed.path.split("/") if segment]
    if not segments or not re.fullmatch(r"\d+-[a-z0-9-]+", segments[0], re.I):
        return [PublicProfileSource(url=url, source_type="other")]
    root = f"{parsed.scheme}://{parsed.hostname}/{segments[0]}"
    return [
        PublicProfileSource(url=f"{root}{suffix}", source_type=source_type)
        for source_type, suffix in DEAKIN_PROFILE_SECTIONS
    ]


def ingestion_read(run: IngestionRun) -> dict[str, object]:
    return {
        **run.model_dump(exclude={"proposal_json", "source_manifest_json"}),
        "proposal": json.loads(run.proposal_json),
        "source_manifest": json.loads(run.source_manifest_json),
    }


def create_ingestion(
    session: Session,
    *,
    source_type: str,
    source_label: str,
    text: str,
    policy: AiHandlingPolicy,
    document_id: UUID | None = None,
    source_url: str = "",
    source_manifest: list[PublicProfileSource] | None = None,
) -> IngestionRun:
    if not text.strip():
        raise HTTPException(status_code=422, detail="No readable text was found in this source")
    extractor = get_career_extractor(policy)
    try:
        proposal = (
            extractor.extract_url(source_url, text, source_label)
            if source_url
            else extractor.extract(text, source_label)
        )
        proposal.source_diagnostics.update(
            {
                "input_characters": len(text),
                "input_quality": "thin" if len(text) < 500 else "substantial",
            }
        )
        if len(text) < 500 and extractor.name != "gemini":
            proposal.warnings.insert(
                0,
                "The page exposed very little readable text. Choose AI allowed for URL Context, "
                "add another source, or upload a PDF/profile export.",
            )
        run = IngestionRun(
            source_type=source_type,
            source_label=source_label,
            source_url=source_url,
            source_manifest_json=json.dumps([item.model_dump() for item in source_manifest or []]),
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
    settings = get_settings()
    session.add(
        AiOperation(
            operation="extract_career_source",
            entity_type="ingestion_run",
            entity_id=str(run.id),
            provider=extractor.name,
            model=settings.gemini_model if extractor.name == "gemini" else "",
            status="completed",
            input_characters=len(text),
            output_characters=len(run.proposal_json),
        )
    )
    record_audit(
        session,
        entity_type="ingestion_run",
        entity_id=run.id,
        action="proposed",
        source=Provenance.AI.value if extractor.name == "gemini" else Provenance.RULE.value,
        details={"source_type": source_type, "provider": extractor.name},
    )
    return run


def merge_source_proposals(
    items: list[tuple[PublicProfileSource, str, CareerExtractionProposal]],
) -> CareerExtractionProposal:
    merged = CareerExtractionProposal()
    profile_fields = ("name", "current_title", "current_organisation", "career_narrative")
    asset_index: dict[tuple[str, int | None], ProposedAsset] = {}
    for source, label, proposal in items:
        source_name = f"{source.source_type}: {label}"
        for field in profile_fields:
            value = getattr(proposal.profile, field).strip()
            if not value:
                continue
            current = getattr(merged.profile, field).strip()
            merged.profile.field_sources.setdefault(field, []).append(source_name)
            if not current:
                setattr(merged.profile, field, value)
            elif current.casefold() != value.casefold():
                merged.conflicts.append(
                    f"Conflicting {field.replace('_', ' ')} values from multiple sources; "
                    f"review the retained value from {merged.profile.field_sources[field][0]}."
                )
        for asset in proposal.assets:
            key = (
                asset.title.strip().casefold(),
                asset.start_date.year if asset.start_date else None,
            )
            existing = asset_index.get(key)
            if existing is None:
                asset.source_labels = [source_name]
                asset.source_urls = [source.url]
                asset_index[key] = asset
                merged.assets.append(asset)
            else:
                existing.source_labels.append(source_name)
                existing.source_urls.append(source.url)
                existing.tags = list(dict.fromkeys([*existing.tags, *asset.tags]))
                existing.themes = list(dict.fromkeys([*existing.themes, *asset.themes]))
                if not existing.description and asset.description:
                    existing.description = asset.description
                if not existing.organisation and asset.organisation:
                    existing.organisation = asset.organisation
        merged.themes.extend(proposal.themes)
        merged.warnings.extend(f"{source_name}: {warning}" for warning in proposal.warnings)
        merged.coverage[source.source_type] = merged.coverage.get(source.source_type, 0) + len(
            proposal.assets
        )
    merged.themes = list(dict.fromkeys(merged.themes))
    merged.conflicts = list(dict.fromkeys(merged.conflicts))
    return merged


def create_multi_url_ingestion(
    session: Session,
    *,
    sources: list[PublicProfileSource],
    policy: AiHandlingPolicy,
) -> IngestionRun:
    extractor = get_career_extractor(policy)
    extracted: list[tuple[PublicProfileSource, str, CareerExtractionProposal]] = []
    input_characters = 0
    for source in sources:
        label, text = fetch_public_page(source.url)
        input_characters += len(text)
        source_proposal = extractor.extract_url(source.url, text, label)
        if not source_proposal.assets:
            source_proposal.warnings.append(
                "This section returned no extractable assets. For research outputs, add the "
                "public Google Scholar or ORCID URL as another source."
            )
        extracted.append((source, label, source_proposal))
    proposal = merge_source_proposals(extracted)
    proposal.source_diagnostics = {
        "source_count": len(sources),
        "locally_visible_characters": input_characters,
        "retrieval": "gemini_url_context" if extractor.name == "gemini" else "local_html",
    }
    run = IngestionRun(
        source_type="url_collection",
        source_label=f"Career source collection ({len(sources)} URLs)",
        source_manifest_json=json.dumps([item.model_dump() for item in sources]),
        ai_handling_policy=policy.value,
        provider=extractor.name,
        proposal_json=proposal.model_dump_json(),
    )
    session.add(run)
    session.flush()
    settings = get_settings()
    session.add(
        AiOperation(
            operation="extract_multi_source_career",
            entity_type="ingestion_run",
            entity_id=str(run.id),
            provider=extractor.name,
            model=settings.gemini_model if extractor.name == "gemini" else "",
            status="completed",
            input_characters=input_characters,
            output_characters=len(run.proposal_json),
        )
    )
    record_audit(
        session,
        entity_type="ingestion_run",
        entity_id=run.id,
        action="multi_source_proposed",
        source=Provenance.AI.value if extractor.name == "gemini" else Provenance.RULE.value,
        details={"source_count": len(sources), "provider": extractor.name},
    )
    return run


def reprocess_ingestion(session: Session, run: IngestionRun) -> IngestionRun:
    if run.status == "applied":
        raise HTTPException(status_code=409, detail="Applied ingestions cannot be reprocessed")
    policy = AiHandlingPolicy(run.ai_handling_policy)
    manifest = [
        PublicProfileSource.model_validate(item) for item in json.loads(run.source_manifest_json)
    ]
    if manifest:
        extractor = get_career_extractor(policy)
        extracted: list[tuple[PublicProfileSource, str, CareerExtractionProposal]] = []
        input_characters = 0
        for source in manifest:
            label, source_text = fetch_public_page(source.url)
            input_characters += len(source_text)
            extracted.append((source, label, extractor.extract_url(source.url, source_text, label)))
        run.provider = extractor.name
        run.proposal_json = merge_source_proposals(extracted).model_dump_json()
        run.status = "ready_for_review"
        run.error_message = ""
        session.add(run)
        settings = get_settings()
        session.add(
            AiOperation(
                operation="reprocess_multi_source_career",
                entity_type="ingestion_run",
                entity_id=str(run.id),
                provider=extractor.name,
                model=settings.gemini_model if extractor.name == "gemini" else "",
                status="completed",
                input_characters=input_characters,
                output_characters=len(run.proposal_json),
            )
        )
        record_audit(
            session,
            entity_type="ingestion_run",
            entity_id=run.id,
            action="reprocessed",
            source=Provenance.AI.value if extractor.name == "gemini" else Provenance.RULE.value,
        )
        return run
    if run.document_id:
        document = session.get(Document, run.document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="Source document is missing")
        text = document.extracted_text
    elif run.source_url:
        _, text = fetch_public_page(run.source_url)
    else:
        raise HTTPException(status_code=422, detail="Ingestion has no reusable source")
    extractor = get_career_extractor(policy)
    proposal = (
        extractor.extract_url(run.source_url, text, run.source_label)
        if run.source_url
        else extractor.extract(text, run.source_label)
    )
    run.provider = extractor.name
    run.proposal_json = proposal.model_dump_json()
    run.status = "ready_for_review"
    run.error_message = ""
    session.add(run)
    settings = get_settings()
    session.add(
        AiOperation(
            operation="reprocess_career_source",
            entity_type="ingestion_run",
            entity_id=str(run.id),
            provider=extractor.name,
            model=settings.gemini_model if extractor.name == "gemini" else "",
            status="completed",
            input_characters=len(text),
            output_characters=len(run.proposal_json),
        )
    )
    record_audit(
        session,
        entity_type="ingestion_run",
        entity_id=run.id,
        action="reprocessed",
        source=Provenance.AI.value if extractor.name == "gemini" else Provenance.RULE.value,
    )
    return run


def save_proposal(session: Session, run: IngestionRun, proposal: CareerExtractionProposal) -> None:
    if run.status == "applied":
        raise HTTPException(status_code=409, detail="Applied ingestions cannot be edited")
    run.proposal_json = proposal.model_dump_json()
    session.add(run)
    record_audit(
        session,
        entity_type="ingestion_run",
        entity_id=run.id,
        action="corrected",
        source=Provenance.USER.value,
    )


def enrich_asset(session: Session, asset: CareerAsset) -> AssetEnrichmentResult:
    extractor = get_career_extractor(AiHandlingPolicy.AI_ALLOWED)
    source = "\n".join([asset.title, asset.description, asset.impact_summary, asset.role])
    result = extractor.enrich(source)
    existing_tags = json.loads(asset.tags_json)
    tags_added = [tag for tag in result.tags if tag not in existing_tags]
    asset.tags_json = json.dumps([*existing_tags, *tags_added])
    asset.updated_at = datetime.now(UTC)
    session.add(asset)
    existing_themes = {item.name.casefold(): item for item in session.exec(select(Theme)).all()}
    linked_ids = {
        link.theme_id
        for link in session.exec(
            select(AssetThemeLink).where(AssetThemeLink.asset_id == asset.id)
        ).all()
    }
    themes_added: list[str] = []
    for name in result.themes:
        clean = name.strip()[:100]
        if not clean:
            continue
        theme = existing_themes.get(clean.casefold())
        if theme is None:
            theme = Theme(name=clean, provenance=Provenance.AI.value)
            session.add(theme)
            session.flush()
            existing_themes[clean.casefold()] = theme
        if theme.id not in linked_ids:
            session.add(
                AssetThemeLink(asset_id=asset.id, theme_id=theme.id, provenance=Provenance.AI.value)
            )
            linked_ids.add(theme.id)
            themes_added.append(theme.name)
    settings = get_settings()
    session.add(
        AiOperation(
            operation="enrich_asset",
            entity_type="career_asset",
            entity_id=str(asset.id),
            provider=extractor.name,
            model=settings.gemini_model if extractor.name == "gemini" else "",
            status="completed",
            input_characters=len(source),
            output_characters=len(result.model_dump_json()),
        )
    )
    record_audit(
        session,
        entity_type="career_asset",
        entity_id=asset.id,
        action="ai_enriched",
        source=Provenance.AI.value if extractor.name == "gemini" else Provenance.RULE.value,
        details={"tags_added": tags_added, "themes_added": themes_added},
    )
    return AssetEnrichmentResult(
        asset_id=asset.id,
        provider=extractor.name,
        tags_added=tags_added,
        themes_added=themes_added,
        summary=result.summary,
        association_suggestions=result.association_suggestions,
    )


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
        evidence_sources = list(zip(item.source_labels, item.source_urls, strict=False))
        if not evidence_sources:
            evidence_sources = [(run.source_label, run.source_url)]
        for evidence_label, evidence_url in evidence_sources:
            session.add(
                EvidenceItem(
                    asset_id=asset.id,
                    document_id=run.document_id,
                    title=evidence_label[:250],
                    description="Source used during reviewed career ingestion.",
                    source_url=evidence_url,
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
