import json
import re
from datetime import UTC, datetime
from threading import Lock
from typing import Any

from app.core.config import get_settings

_write_lock = Lock()
_SECRET_PATTERN = re.compile(r"(?i)(api[_ -]?key|x-goog-api-key)([=: ]+)([^\s,;]+)")


def write_profile_diagnostic(event: str, **details: Any) -> None:
    """Append a safe JSONL event without storing source content or credentials."""
    settings = get_settings()
    log_dir = settings.data_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event": event,
        **details,
    }
    encoded = json.dumps(record, ensure_ascii=False, default=str)
    encoded = _SECRET_PATTERN.sub(r"\1\2[REDACTED]", encoded)
    with _write_lock, (log_dir / "profile-ingestion.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(f"{encoded}\n")
