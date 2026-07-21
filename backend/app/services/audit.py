import json
from typing import Any
from uuid import UUID

from sqlmodel import Session

from app.models.career import AuditEvent


def record_audit(
    session: Session,
    *,
    entity_type: str,
    entity_id: UUID | str,
    action: str,
    source: str = "user",
    details: dict[str, Any] | None = None,
) -> None:
    event = AuditEvent(
        entity_type=entity_type,
        entity_id=str(entity_id),
        action=action,
        source=source,
        details_json=json.dumps(details or {}, default=str, sort_keys=True),
    )
    session.add(event)
