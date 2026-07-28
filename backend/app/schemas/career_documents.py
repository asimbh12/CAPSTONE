from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CareerDocumentGenerate(BaseModel):
    document_type: str = Field(
        pattern=(
            "^(professional_biography|executive_profile|linkedin_about|academic_cv|"
            "executive_cv|board_cv|grant_cv|capability_statement)$"
        )
    )
    title: str = Field(min_length=1, max_length=300)
    audience: str = Field(default="", max_length=300)
    purpose: str = Field(default="", max_length=2_000)
    tone: str = Field(default="executive", pattern="^(executive|academic|accessible)$")
    asset_ids: list[UUID] = Field(default_factory=list, max_length=100)


class CareerDocumentUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    content: str = Field(min_length=20, max_length=100_000)


class CareerDocumentRead(BaseModel):
    id: UUID
    document_type: str
    title: str
    audience: str
    purpose: str
    tone: str
    content: str
    provider: str
    asset_ids: list[UUID]
    unsupported_claims: list[str]
    created_at: datetime
    updated_at: datetime


class CareerDocumentList(BaseModel):
    items: list[CareerDocumentRead]
    total: int


class ProviderCareerDocument(BaseModel):
    content: str = Field(min_length=200, max_length=100_000)
    unsupported_claims: list[str] = Field(default_factory=list, max_length=50)
