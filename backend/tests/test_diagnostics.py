import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.services import diagnostics


def test_profile_diagnostic_is_jsonl_and_redacts_credentials(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(diagnostics, "get_settings", lambda: SimpleNamespace(data_root=tmp_path))

    diagnostics.write_profile_diagnostic(
        "page_failed",
        url="https://example.org/profile",
        error="x-goog-api-key=secret-value request failed",
    )

    record = json.loads((tmp_path / "logs" / "profile-ingestion.jsonl").read_text())
    assert record["event"] == "page_failed"
    assert record["url"] == "https://example.org/profile"
    assert "secret-value" not in record["error"]
