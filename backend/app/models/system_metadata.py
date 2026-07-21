from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class SystemMetadata(SQLModel, table=True):
    __tablename__ = "system_metadata"

    key: str = Field(primary_key=True, max_length=100)
    value: str
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC), nullable=False)

