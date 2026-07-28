from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SystemCheck(BaseModel):
    key: str
    label: str
    status: Literal["pass", "warning", "fail"]
    message: str
    details: list[str] = Field(default_factory=list)


class SystemReadiness(BaseModel):
    status: Literal["ready", "attention", "blocked"]
    checked_at: datetime
    passed: int
    warnings: int
    failures: int
    checks: list[SystemCheck]
