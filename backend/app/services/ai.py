import re
from abc import ABC, abstractmethod
from datetime import date

from app.core.config import Settings, get_settings
from app.models.career import AiHandlingPolicy
from app.schemas.ingestion import CareerExtractionProposal, ProposedAsset, ProposedProfile


class CareerExtractor(ABC):
    name: str

    @abstractmethod
    def extract(self, text: str, source_label: str) -> CareerExtractionProposal: ...


class DeterministicCareerExtractor(CareerExtractor):
    name = "deterministic"

    def extract(self, text: str, source_label: str) -> CareerExtractionProposal:
        lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
        lines = [line for line in lines if line]
        name = lines[0][:200] if lines else ""
        assets: list[ProposedAsset] = []
        pattern = re.compile(
            r"(?P<start>(?:19|20)\d{2})(?:\s*[-–—]\s*(?P<end>(?:19|20)\d{2}|present))?", re.I
        )
        for index, line in enumerate(lines[:250]):
            match = pattern.search(line)
            if not match or len(line) > 300:
                continue
            title = pattern.sub("", line).strip(" -–—|,") or "Professional experience"
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
                    themes=[],
                    tags=["imported-from-career-document"],
                )
            )
        warning = (
            "Offline extraction found no dated entries; enable Gemini or edit the "
            "proposal manually."
            if not assets
            else "Review dates and titles before applying; offline extraction is "
            "intentionally conservative."
        )
        return CareerExtractionProposal(
            profile=ProposedProfile(
                name=name, career_narrative=f"Career information extracted from {source_label}."
            ),
            assets=assets[:50],
            warnings=[warning],
        )


class GeminiCareerExtractor(CareerExtractor):
    name = "gemini"

    def __init__(self, settings: Settings) -> None:
        from google import genai

        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model

    def extract(self, text: str, source_label: str) -> CareerExtractionProposal:
        prompt = (
            "Extract only explicitly supported public professional facts from this career source. "
            "Do not infer achievements, dates, employers, impact, or identity. Propose a profile, "
            "dated career assets, concise AI-managed tags and themes. Use empty values "
            "when unknown. "
            f"Source: {source_label}\n\n{text[:120_000]}"
        )
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": CareerExtractionProposal,
                "temperature": 0,
            },
        )
        return CareerExtractionProposal.model_validate_json(response.text or "{}")


def get_career_extractor(policy: AiHandlingPolicy) -> CareerExtractor:
    settings = get_settings()
    if policy != AiHandlingPolicy.AI_ALLOWED:
        return DeterministicCareerExtractor()
    if settings.ai_provider.lower() == "gemini" and settings.gemini_api_key:
        return GeminiCareerExtractor(settings)
    return DeterministicCareerExtractor()
