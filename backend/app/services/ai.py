import re
from abc import ABC, abstractmethod
from datetime import date

from app.core.config import Settings, get_settings
from app.models.career import AiHandlingPolicy
from app.schemas.ingestion import (
    AssetEnrichment,
    CareerExtractionProposal,
    ProposedAsset,
    ProposedProfile,
    ProviderCareerExtractionProposal,
)


class CareerExtractor(ABC):
    name: str
    model: str = ""

    @abstractmethod
    def extract(self, text: str, source_label: str) -> CareerExtractionProposal: ...

    def extract_url(
        self, url: str, fallback_text: str, source_label: str
    ) -> CareerExtractionProposal:
        return self.extract(fallback_text, source_label)

    @abstractmethod
    def enrich(self, text: str) -> AssetEnrichment: ...


class DeterministicCareerExtractor(CareerExtractor):
    name = "deterministic"

    def extract(self, text: str, source_label: str) -> CareerExtractionProposal:
        lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
        lines = [line for line in lines if line]
        name = lines[0][:200] if lines else ""
        assets: list[ProposedAsset] = []
        pattern = re.compile(
            r"(?<![A-Za-z0-9:/])(?P<start>(?:19|20)\d{2})"
            r"(?:\s*[-–—]\s*(?P<end>(?:19|20)\d{2}|present))?(?!\d)",
            re.I,
        )
        for index, line in enumerate(lines[:500]):
            line_without_urls = re.sub(r"https?://\S+", "", line, flags=re.I)
            match = pattern.search(line_without_urls)
            if not match or len(line) > 500:
                continue
            title = (
                pattern.sub("", line_without_urls).strip(" -–—|,")
                or "Professional experience"
            )
            detail = lines[index + 1] if index + 1 < len(lines) else ""
            assets.append(
                ProposedAsset(
                    title=title[:300],
                    description=detail[:2_000],
                    role=title[:250],
                    start_date=date(int(match.group("start")), 1, 1),
                    end_date=None
                    if not match.group("end") or match.group("end").lower() == "present"
                    else date(int(match.group("end")), 12, 31),
                    tags=["imported-from-career-document"],
                )
            )
        warning = (
            "Offline extraction found no dated entries; choose AI allowed for comprehensive "
            "analysis or edit the proposal manually."
            if not assets
            else "Local extraction captures date-shaped entries only. Choose AI allowed to analyse "
            "undated achievements, qualifications, publications, grants and other sections."
        )
        return CareerExtractionProposal(
            profile=ProposedProfile(
                name=name, career_narrative=f"Career information extracted from {source_label}."
            ),
            assets=assets[:100],
            warnings=[warning],
        )

    def enrich(self, text: str) -> AssetEnrichment:
        words = re.findall(r"[A-Za-z][A-Za-z-]{3,}", text.lower())
        excluded = {"with", "from", "that", "this", "were", "have", "public", "professional"}
        terms = [word for word in words if word not in excluded]
        ranked = sorted(set(terms), key=lambda item: (-terms.count(item), item))[:8]
        return AssetEnrichment(tags=ranked, summary="Offline keyword enrichment completed.")


class GeminiCareerExtractor(CareerExtractor):
    name = "gemini"

    def __init__(self, settings: Settings) -> None:
        from google import genai

        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model

    @staticmethod
    def _instructions() -> str:
        return (
            "Create a comprehensive, source-grounded inventory of every explicitly stated public "
            "professional fact. Include employment, appointments, acting roles, education, "
            "qualifications, awards, grants, funded projects, publications, patents, research "
            "themes, teaching, supervision, committees, boards, memberships, industry and "
            "government engagement, media, service, leadership, and quantified impact. Create "
            "separate assets for distinct facts even when no date is stated; dates are optional. "
            "Preserve organisations, roles, descriptions, outcomes and metrics in substance. Do "
            "not infer or embellish. Return up to 150 distinct assets, plus concise tags and "
            "themes."
        )

    def extract(self, text: str, source_label: str) -> CareerExtractionProposal:
        response = self.client.models.generate_content(
            model=self.model,
            contents=f"{self._instructions()}\n\nSource: {source_label}\n\n{text[:120_000]}",
            config={
                "response_mime_type": "application/json",
                "response_schema": ProviderCareerExtractionProposal,
                "temperature": 0,
            },
        )
        provider_result = ProviderCareerExtractionProposal.model_validate_json(
            response.text or "{}"
        )
        return CareerExtractionProposal.model_validate(provider_result.model_dump())

    def extract_url(
        self, url: str, fallback_text: str, source_label: str
    ) -> CareerExtractionProposal:
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=(
                    f"{self._instructions()} Use URL context to read the URL. If retrieval fails, "
                    f"explain it in warnings.\n\nSource: {source_label}\nURL: {url}"
                ),
                config={
                    "tools": [{"url_context": {}}],
                    "response_mime_type": "application/json",
                    "response_schema": ProviderCareerExtractionProposal,
                    "temperature": 0,
                },
            )
            provider_result = ProviderCareerExtractionProposal.model_validate_json(
                response.text or "{}"
            )
            proposal = CareerExtractionProposal.model_validate(provider_result.model_dump())
            proposal.source_diagnostics = {
                "retrieval": "gemini_url_context",
                "locally_visible_characters": len(fallback_text),
            }
            return proposal
        except Exception:
            proposal = self.extract(fallback_text, source_label)
            proposal.warnings.insert(
                0,
                "Gemini URL Context was unavailable; analysis used only text visible to the local "
                "page reader.",
            )
            proposal.source_diagnostics = {
                "retrieval": "local_html_fallback",
                "locally_visible_characters": len(fallback_text),
            }
            return proposal

    def enrich(self, text: str) -> AssetEnrichment:
        response = self.client.models.generate_content(
            model=self.model,
            contents=(
                "Using only the supplied career asset facts, produce concise derived tags, "
                "strategic themes, a factual summary, and non-binding association suggestions. "
                "Do not invent metrics, outcomes, credentials, dates, or responsibilities.\n\n"
                f"{text[:30_000]}"
            ),
            config={
                "response_mime_type": "application/json",
                "response_schema": AssetEnrichment,
                "temperature": 0,
            },
        )
        return AssetEnrichment.model_validate_json(response.text or "{}")


def get_career_extractor(policy: AiHandlingPolicy) -> CareerExtractor:
    settings = get_settings()
    if policy != AiHandlingPolicy.AI_ALLOWED:
        return DeterministicCareerExtractor()
    if settings.ai_provider.lower() == "gemini" and settings.gemini_api_key:
        return GeminiCareerExtractor(settings)
    return DeterministicCareerExtractor()
