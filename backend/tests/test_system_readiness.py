from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlmodel import Session

from app.db.session import get_engine
from app.models.career import AiOperation, IngestionRun


def _mark_migrations_current() -> None:
    with get_engine().begin() as connection:
        connection.execute(
            text("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL)")
        )
        connection.execute(text("DELETE FROM alembic_version"))
        connection.execute(
            text("INSERT INTO alembic_version (version_num) VALUES ('20260722_0010')")
        )


def _check(response: dict[str, object], key: str) -> dict[str, object]:
    checks = response["checks"]
    assert isinstance(checks, list)
    return next(item for item in checks if isinstance(item, dict) and item["key"] == key)


def test_system_readiness_checks_release_critical_local_services(client: TestClient) -> None:
    _mark_migrations_current()

    response = client.get("/api/system/readiness")

    assert response.status_code == 200
    report = response.json()
    assert report["status"] == "attention"
    assert report["failures"] == 0
    assert _check(report, "database_integrity")["status"] == "pass"
    assert _check(report, "database_migrations")["status"] == "pass"
    assert _check(report, "local_storage")["status"] == "pass"
    assert _check(report, "document_integrity")["status"] == "pass"
    assert _check(report, "ai_data_policy")["status"] == "pass"
    assert _check(report, "recoverable_backup")["status"] == "warning"


def test_system_readiness_blocks_release_when_document_checksum_changes(
    client: TestClient, tmp_path: Path
) -> None:
    _mark_migrations_current()
    uploaded = client.post(
        "/api/documents",
        files={"file": ("public.txt", b"Public professional record", "text/plain")},
        data={"ai_handling_policy": "local_only", "confirmed_public_information": "true"},
    )
    assert uploaded.status_code == 200
    stored = next((tmp_path / "data" / "originals").rglob("public.txt"))
    stored.write_text("Changed outside CAPSTONE", encoding="utf-8")

    report = client.get("/api/system/readiness").json()

    assert report["status"] == "blocked"
    check = _check(report, "document_integrity")
    assert check["status"] == "fail"
    assert any("Checksum mismatch" in detail for detail in check["details"])


def test_system_readiness_reports_schema_revision_mismatch(client: TestClient) -> None:
    report = client.get("/api/system/readiness").json()

    assert report["status"] == "blocked"
    check = _check(report, "database_migrations")
    assert check["status"] == "fail"
    assert any("Expected: 20260722_0010" in detail for detail in check["details"])


def test_system_readiness_detects_restricted_ai_use_and_recoverable_failure(
    client: TestClient,
) -> None:
    _mark_migrations_current()
    with Session(get_engine()) as session:
        run = IngestionRun(
            source_type="document",
            source_label="Local-only source",
            ai_handling_policy="local_only",
            provider="deterministic",
            status="failed",
            error_message="Provider operation was interrupted",
        )
        session.add(run)
        session.flush()
        session.add(
            AiOperation(
                operation="career_extraction",
                entity_type="ingestion_run",
                entity_id=str(run.id),
                provider="gemini",
                status="completed",
            )
        )
        session.commit()

    report = client.get("/api/system/readiness").json()

    assert report["status"] == "blocked"
    policy = _check(report, "ai_data_policy")
    assert policy["status"] == "fail"
    assert any("External AI used for restricted ingestion" in item for item in policy["details"])
    recovery = _check(report, "failed_operations")
    assert recovery["status"] == "warning"
    assert recovery["details"] == ["Local-only source"]
