import json
import logging
from html import escape
from io import BytesIO
from typing import Any
from uuid import UUID

from docx import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor
from fastapi import HTTPException
from reportlab.lib.colors import HexColor  # type: ignore[import-untyped]
from reportlab.lib.pagesizes import A4  # type: ignore[import-untyped]
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # type: ignore[import-untyped]
from reportlab.lib.units import mm  # type: ignore[import-untyped]
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer  # type: ignore[import-untyped]
from sqlmodel import Session, col, select

from app.core.config import get_settings
from app.models.career import CareerAsset, CareerDocument, CareerProfile
from app.schemas.career_documents import (
    CareerDocumentGenerate,
    CareerDocumentRead,
    ProviderCareerDocument,
)
from app.services.applications import _add_docx_markdown, _add_pdf_markdown, _asset_context

logger = logging.getLogger(__name__)

TYPE_LABELS = {
    "professional_biography": "Professional biography",
    "executive_profile": "Executive profile",
    "linkedin_about": "LinkedIn About",
}


def read_document(item: CareerDocument) -> CareerDocumentRead:
    return CareerDocumentRead(
        **item.model_dump(exclude={"asset_ids_json", "unsupported_claims_json"}),
        asset_ids=json.loads(item.asset_ids_json),
        unsupported_claims=json.loads(item.unsupported_claims_json),
    )


def get_or_404(session: Session, document_id: UUID) -> CareerDocument:
    item = session.get(CareerDocument, document_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Career document not found")
    return item


def _fallback(
    payload: CareerDocumentGenerate,
    profile: CareerProfile | None,
    assets: list[CareerAsset],
) -> str:
    name = profile.name if profile and profile.name else "Career professional"
    current = " at ".join(
        value
        for value in (
            profile.current_title if profile else "",
            profile.current_organisation if profile else "",
        )
        if value
    )
    narrative = (
        profile.career_narrative or profile.career_mission
        if profile
        else ""
    )
    evidence = [
        asset.impact_summary or asset.description or asset.title for asset in assets[:8]
    ]
    if payload.document_type == "linkedin_about":
        return "\n\n".join(
            part
            for part in (
                f"I am {name}{f', {current}' if current else ''}.",
                narrative,
                "My work includes:\n" + "\n".join(f"- {value}" for value in evidence),
                payload.purpose,
            )
            if part
        )
    heading = TYPE_LABELS[payload.document_type]
    return "\n\n".join(
        part
        for part in (
            f"# {heading}",
            f"{name}{f' is {current}' if current else ''}. {narrative}".strip(),
            "## Selected impact\n" + "\n".join(f"- {value}" for value in evidence),
            f"## Intended use\n{payload.purpose}" if payload.purpose else "",
        )
        if part
    )


def _provider_content(
    payload: CareerDocumentGenerate,
    profile: CareerProfile | None,
    assets: list[CareerAsset],
) -> ProviderCareerDocument | None:
    settings = get_settings()
    if settings.ai_provider.casefold() != "gemini" or not settings.gemini_api_key:
        return None
    profile_data = profile.model_dump(mode="json") if profile else {}
    audience = payload.audience or "general professional audience"
    purpose = payload.purpose or "reusable career communication"
    prompt = f"""
Write a polished {TYPE_LABELS[payload.document_type]} using only the verified public facts below.
Never invent roles, dates, qualifications, awards, metrics, outcomes or endorsements. Put any
requested idea that lacks evidence into unsupported_claims instead of stating it. Use clean
Markdown headings, paragraphs and bullets; no tables. Audience: {audience}. Purpose: {purpose}.
Tone: {payload.tone}. Make the document specific, cohesive and impact-led rather than an asset
list.

PROFILE: {json.dumps(profile_data, ensure_ascii=False)}
VERIFIED ASSETS: {_asset_context(assets)[:120_000]}
"""
    try:
        from google import genai

        response = genai.Client(api_key=settings.gemini_api_key).models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": ProviderCareerDocument,
                "temperature": 0.25,
            },
        )
        return ProviderCareerDocument.model_validate_json(response.text or "{}")
    except Exception:
        logger.exception("Gemini career-document generation failed; using local fallback")
        return None


def generate(session: Session, payload: CareerDocumentGenerate) -> CareerDocument:
    profile = session.exec(select(CareerProfile)).first()
    query = select(CareerAsset).where(CareerAsset.status == "active")
    if payload.asset_ids:
        query = query.where(col(CareerAsset.id).in_(payload.asset_ids))
    assets = list(
        session.exec(
            query.order_by(col(CareerAsset.start_date).desc(), col(CareerAsset.created_at).desc())
        ).all()
    )
    if not assets:
        raise HTTPException(
            status_code=409,
            detail="Add at least one active career asset before generating a document",
        )
    provider_result = _provider_content(payload, profile, assets)
    item = CareerDocument(
        document_type=payload.document_type,
        title=payload.title,
        audience=payload.audience,
        purpose=payload.purpose,
        tone=payload.tone,
        content=provider_result.content if provider_result else _fallback(payload, profile, assets),
        provider="gemini" if provider_result else "grounded_template",
        asset_ids_json=json.dumps([str(asset.id) for asset in assets]),
        unsupported_claims_json=json.dumps(
            provider_result.unsupported_claims if provider_result else []
        ),
    )
    session.add(item)
    return item


def export_document(item: CareerDocument, format_name: str) -> bytes:
    if format_name == "docx":
        document = DocxDocument()
        section = document.sections[0]
        section.top_margin = section.bottom_margin = Inches(0.8)
        section.left_margin = section.right_margin = Inches(0.9)
        document.styles["Normal"].font.name = "Calibri"
        document.styles["Normal"].font.size = Pt(11)
        title = document.add_heading(item.title, 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title.runs[0].font.color.rgb = RGBColor(31, 78, 121)
        if item.audience:
            subtitle = document.add_paragraph(item.audience, style="Subtitle")
            subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _add_docx_markdown(document, item.content)
        buffer = BytesIO()
        document.save(buffer)
        return buffer.getvalue()
    buffer = BytesIO()
    pdf = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=item.title,
    )
    sample = getSampleStyleSheet()
    styles: dict[str, ParagraphStyle] = {
        "heading2": ParagraphStyle(
            "CareerHeading2", parent=sample["Heading2"], textColor=HexColor("#2E74B5")
        ),
        "heading3": ParagraphStyle(
            "CareerHeading3", parent=sample["Heading3"], textColor=HexColor("#1F4D78")
        ),
        "body": ParagraphStyle(
            "CareerBody", parent=sample["BodyText"], fontSize=10.5, leading=14, spaceAfter=7
        ),
        "bullet": ParagraphStyle(
            "CareerBullet", parent=sample["BodyText"], leftIndent=16, firstLineIndent=-10
        ),
        "subtitle": ParagraphStyle(
            "CareerSubtitle",
            parent=sample["BodyText"],
            alignment=1,
            textColor=HexColor("#5B6573"),
            fontSize=11,
            leading=14,
        ),
    }
    story: list[Any] = [
        Paragraph(escape(item.title), sample["Title"]),
        Paragraph(escape(item.audience), styles["subtitle"])
        if item.audience
        else Spacer(1, 4),
        Spacer(1, 10),
    ]
    _add_pdf_markdown(story, item.content, styles)
    pdf.build(story)
    return buffer.getvalue()
