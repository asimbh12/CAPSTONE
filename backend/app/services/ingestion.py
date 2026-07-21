import ipaddress
import json
import re
import socket
from datetime import UTC, datetime
from html import unescape
from html.parser import HTMLParser
from time import monotonic
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse
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
    ProposedProfile,
    PublicProfileSource,
)
from app.services.ai import get_career_extractor
from app.services.audit import record_audit
from app.services.diagnostics import write_profile_diagnostic

DEAKIN_PROFILE_SECTIONS = (
    ("profile", ""),
    ("research_outputs", "/publications"),
    ("research_grants", "/grants"),
    ("professional_activities", "/professional"),
    ("teaching_supervision", "/teaching"),
)
MAX_DISCOVERED_PAGES = 20
PROFILE_LINK_TERMS = {
    "about",
    "appointment",
    "award",
    "biography",
    "education",
    "employment",
    "experience",
    "grant",
    "media",
    "membership",
    "professional",
    "profile",
    "project",
    "publication",
    "qualification",
    "research",
    "service",
    "supervision",
    "teaching",
}


class _ProfileLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href = ""
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() == "a":
            self._href = dict(attrs).get("href") or ""
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() == "a" and self._href:
            self.links.append((self._href, " ".join(self._text)))
            self._href = ""
            self._text = []


def expand_public_profile_sources(url: str) -> list[PublicProfileSource]:
    """Expand supported profile hubs into their public, first-party section pages."""
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").casefold()
    if hostname.endswith("scholar.google.com") or hostname.startswith("scholar.google."):
        query = parse_qs(parsed.query)
        if parsed.path == "/citations" and query.get("user"):
            pages: list[PublicProfileSource] = []
            for offset in range(0, 1_000, 100):
                page_query = {key: values[-1] for key, values in query.items()}
                page_query.update({"cstart": str(offset), "pagesize": "100"})
                page_url = urlunparse(parsed._replace(query=urlencode(page_query)))
                pages.append(PublicProfileSource(url=page_url, source_type="google_scholar"))
            return pages
    if hostname not in {"experts.deakin.edu.au", "www.experts.deakin.edu.au"}:
        return [PublicProfileSource(url=url, source_type="other")]
    segments = [segment for segment in parsed.path.split("/") if segment]
    if not segments or not re.fullmatch(r"\d+-[a-z0-9-]+", segments[0], re.I):
        return [PublicProfileSource(url=url, source_type="other")]
    root = f"{parsed.scheme}://{parsed.hostname}/{segments[0]}"
    return [
        PublicProfileSource(url=f"{root}{suffix}", source_type=source_type)
        for source_type, suffix in DEAKIN_PROFILE_SECTIONS
    ]


def discover_linked_profile_sources(
    source: PublicProfileSource, html: str
) -> list[PublicProfileSource]:
    """Discover relevant, same-site pages linked by a public profile hub."""
    parser = _ProfileLinkParser()
    parser.feed(html)
    base = urlparse(source.url)
    hostname = (base.hostname or "").casefold()
    candidates: list[tuple[int, str]] = []
    for href, anchor in parser.links:
        absolute = urljoin(source.url, href)
        parsed = urlparse(absolute)
        if parsed.scheme not in {"http", "https"} or (parsed.hostname or "").casefold() != hostname:
            continue
        base_path = base.path.rstrip("/")
        if base_path and parsed.path != base_path and not parsed.path.startswith(f"{base_path}/"):
            continue
        if parsed.path == base.path and parsed.query == base.query:
            continue
        searchable = f"{parsed.path} {parsed.query} {anchor}".casefold()
        score = sum(term in searchable for term in PROFILE_LINK_TERMS)
        is_pagination = bool(re.search(r"(?:page|start|offset|cstart)=\d+", parsed.query, re.I))
        if not score and not is_pagination:
            continue
        clean = urlunparse(parsed._replace(fragment=""))
        candidates.append((score + (2 if is_pagination else 0), clean))
    ordered = [source]
    seen = {source.url}
    for _, url in sorted(candidates, key=lambda item: (-item[0], item[1])):
        if url not in seen:
            ordered.append(PublicProfileSource(url=url, source_type="profile_section"))
            seen.add(url)
        if len(ordered) >= MAX_DISCOVERED_PAGES:
            break
    return ordered


def build_profile_source_manifest(source: PublicProfileSource) -> list[PublicProfileSource]:
    """Build the bounded set of pages that should be analysed for one supplied profile URL."""
    expanded = expand_public_profile_sources(source.url)
    if len(expanded) > 1:
        write_profile_diagnostic(
            "manifest_expanded",
            submitted_url=source.url,
            source_type=source.source_type,
            pages_discovered=len(expanded),
            discovered_urls=[item.url for item in expanded],
        )
        return expanded
    try:
        _, _, html = fetch_public_document(source.url)
    except HTTPException as exc:
        write_profile_diagnostic(
            "manifest_fetch_failed",
            submitted_url=source.url,
            source_type=source.source_type,
            error=str(exc.detail),
        )
        return [source]
    discovered = discover_linked_profile_sources(source, html)
    write_profile_diagnostic(
        "manifest_discovered",
        submitted_url=source.url,
        source_type=source.source_type,
        pages_discovered=len(discovered),
        discovered_urls=[item.url for item in discovered],
    )
    return discovered


def is_thin_scholar_continuation(source: PublicProfileSource, text: str) -> bool:
    raw_offset = parse_qs(urlparse(source.url).query).get("cstart", ["0"])[0]
    offset = int(raw_offset) if raw_offset.isdigit() else 0
    return source.source_type == "google_scholar" and offset > 0 and len(text) < 5_000


def extract_google_scholar_rows(
    html: str, source_label: str
) -> CareerExtractionProposal | None:
    """Extract every visible Scholar result row without asking an LLM to summarize the list."""
    rows = re.findall(r'<tr[^>]+class="[^"]*gsc_a_tr[^"]*"[^>]*>(.*?)</tr>', html, re.I | re.S)
    assets: list[ProposedAsset] = []
    for row in rows:
        title_match = re.search(
            r'<a[^>]+class="[^"]*gsc_a_at[^"]*"[^>]*>(.*?)</a>', row, re.I | re.S
        )
        if not title_match:
            continue
        title = unescape(re.sub(r"<[^>]+>", "", title_match.group(1))).strip()
        details = [
            unescape(re.sub(r"<[^>]+>", "", item)).strip()
            for item in re.findall(
                r'<div[^>]+class="[^"]*gs_gray[^"]*"[^>]*>(.*?)</div>', row, re.I | re.S
            )
        ]
        year_match = re.search(r"\b((?:19|20)\d{2})\b", row)
        assets.append(
            ProposedAsset(
                title=title[:300],
                description=" · ".join(item for item in details if item)[:2_000],
                category="Research Output",
                role="Author",
                start_date=(
                    datetime(int(year_match.group(1)), 1, 1).date() if year_match else None
                ),
                tags=["publication", "google-scholar"],
            )
        )
    if not assets:
        return None
    name = source_label.removesuffix(" - Google Scholar").strip()
    return CareerExtractionProposal(
        profile=ProposedProfile(name=name),
        assets=assets,
        source_diagnostics={
            "retrieval": "google_scholar_structured_html",
            "structured_rows": len(assets),
        },
    )


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
    diagnostic_id = f"profile-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')}"
    extracted: list[tuple[PublicProfileSource, str, CareerExtractionProposal]] = []
    input_characters = 0
    processed_sources: list[PublicProfileSource] = []
    pending = list(sources[:MAX_DISCOVERED_PAGES])
    queued_urls = {source.url for source in pending}
    write_profile_diagnostic(
        "ingestion_started",
        diagnostic_id=diagnostic_id,
        provider=extractor.name,
        model=extractor.model,
        policy=policy.value,
        initial_pages=len(pending),
        urls=[source.url for source in pending],
    )
    for source in pending:
        started = monotonic()
        local_fetch = "succeeded"
        local_error = ""
        try:
            label, text, html = fetch_public_document(source.url)
            if source.source_type not in {"google_scholar", "orcid"}:
                for linked in discover_linked_profile_sources(source, html)[1:]:
                    if linked.url not in queued_urls and len(pending) < MAX_DISCOVERED_PAGES:
                        pending.append(linked)
                        queued_urls.add(linked.url)
        except HTTPException as exc:
            local_fetch = "failed"
            local_error = str(exc.detail)
            if extractor.name != "gemini":
                write_profile_diagnostic(
                    "page_failed",
                    diagnostic_id=diagnostic_id,
                    url=source.url,
                    source_type=source.source_type,
                    stage="local_fetch",
                    error=local_error,
                )
                raise
            label, text = source.url, ""
        input_characters += len(text)
        if is_thin_scholar_continuation(source, text):
            write_profile_diagnostic(
                "pagination_stopped",
                diagnostic_id=diagnostic_id,
                url=source.url,
                source_type=source.source_type,
                reason="thin_continuation_page",
                locally_visible_characters=len(text),
                remaining_pages=len(pending) - len(processed_sources),
            )
            break
        try:
            source_proposal = (
                extract_google_scholar_rows(html, label)
                if source.source_type == "google_scholar" and local_fetch == "succeeded"
                else None
            ) or extractor.extract_url(source.url, text, label)
        except Exception as exc:
            write_profile_diagnostic(
                "page_failed",
                diagnostic_id=diagnostic_id,
                url=source.url,
                source_type=source.source_type,
                stage="extraction",
                error_type=type(exc).__name__,
                error=str(exc)[:1_000],
                elapsed_ms=round((monotonic() - started) * 1_000),
            )
            raise
        if not source_proposal.assets:
            source_proposal.warnings.append(
                "This section returned no extractable assets. For research outputs, add the "
                "public Google Scholar or ORCID URL as another source."
            )
        extracted.append((source, label, source_proposal))
        processed_sources.append(source)
        raw_offset = parse_qs(urlparse(source.url).query).get("cstart", ["0"])[0]
        scholar_offset = int(raw_offset) if raw_offset.isdigit() else 0
        write_profile_diagnostic(
            "page_completed",
            diagnostic_id=diagnostic_id,
            url=source.url,
            source_type=source.source_type,
            label=label,
            local_fetch=local_fetch,
            local_fetch_error=local_error,
            locally_visible_characters=len(text),
            extraction_diagnostics=source_proposal.source_diagnostics,
            proposed_assets=len(source_proposal.assets),
            warnings=source_proposal.warnings,
            elapsed_ms=round((monotonic() - started) * 1_000),
        )
        if (
            source.source_type == "google_scholar"
            and scholar_offset > 0
            and not source_proposal.assets
        ):
            write_profile_diagnostic(
                "pagination_stopped",
                diagnostic_id=diagnostic_id,
                url=source.url,
                source_type=source.source_type,
                reason="empty_continuation_page",
                remaining_pages=len(pending) - len(processed_sources),
            )
            break
    proposal = merge_source_proposals(extracted)
    proposal.source_diagnostics = {
        "source_count": len(processed_sources),
        "pages_discovered": len(pending),
        "locally_visible_characters": input_characters,
        "retrieval": "gemini_url_context" if extractor.name == "gemini" else "local_html",
    }
    run = IngestionRun(
        source_type="url_collection",
        source_label=f"Career source collection ({len(processed_sources)} pages analysed)",
        source_manifest_json=json.dumps([item.model_dump() for item in processed_sources]),
        ai_handling_policy=policy.value,
        provider=extractor.name,
        proposal_json=proposal.model_dump_json(),
    )
    session.add(run)
    session.flush()
    write_profile_diagnostic(
        "ingestion_completed",
        diagnostic_id=diagnostic_id,
        ingestion_run_id=str(run.id),
        provider=extractor.name,
        pages_discovered=len(pending),
        pages_processed=len(processed_sources),
        merged_assets=len(proposal.assets),
        coverage=proposal.coverage,
        warnings=proposal.warnings,
    )
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
        details={"source_count": len(processed_sources), "provider": extractor.name},
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
            try:
                label, source_text = fetch_public_page(source.url)
            except HTTPException:
                if extractor.name != "gemini":
                    raise
                label, source_text = source.url, ""
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


def fetch_public_document(url: str) -> tuple[str, str, str]:
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
    return label[:500], re.sub(r"\n\s*\n+", "\n", text).strip(), html


def fetch_public_page(url: str) -> tuple[str, str]:
    label, text, _ = fetch_public_document(url)
    return label, text


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
