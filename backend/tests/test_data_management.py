import json
import sqlite3
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient


def _import_payload() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "profile": {
            "name": "Imported Professional",
            "current_title": "Engineer",
            "current_organisation": "Public Organisation",
            "career_mission": "Create public benefit",
            "career_narrative": "",
        },
        "themes": [{"name": "Innovation", "description": ""}],
        "goals": [],
        "organisations": [],
        "people": [],
        "assets": [
            {
                "title": "Public innovation programme",
                "description": "",
                "category": "Innovation Asset",
                "subcategory": "",
                "start_date": "2024-01-01",
                "end_date": None,
                "date_precision": "day",
                "status": "active",
                "impact_summary": "",
                "organisation_id": None,
                "role": "",
                "visibility": "public",
                "tags": [],
                "keywords": [],
                "theme_ids": [],
            }
        ],
    }


def test_import_requires_dry_run_and_can_apply(client: TestClient) -> None:
    request = {
        "confirmed_public_information": True,
        "mode": "dry_run",
        "payload": _import_payload(),
    }
    dry_run = client.post("/api/data/import", json=request)
    assert dry_run.status_code == 200
    assert dry_run.json()["valid"] is True
    assert dry_run.json()["applied"] is False

    request["mode"] = "apply"
    applied = client.post("/api/data/import", json=request)
    assert applied.status_code == 200
    assert applied.json()["applied"] is True
    assert client.get("/api/assets").json()["total"] == 1

    export = client.get("/api/data/export")
    assert export.status_code == 200
    assert export.json()["schema_version"] == "1.0"
    assert export.json()["assets"][0]["title"] == "Public innovation programme"


def test_backup_contains_database_and_checksum_manifest(client: TestClient) -> None:
    client.put("/api/profile", json={"name": "Recoverable Professional"})
    backup_response = client.post("/api/data/backups")
    assert backup_response.status_code == 200
    assert backup_response.json()["verified"] is True
    assert backup_response.json()["database_integrity"] == "ok"
    filename = backup_response.json()["filename"]
    verification = client.get(f"/api/data/backups/{filename}/verify")
    assert verification.status_code == 200
    assert verification.json()["valid"] is True
    download = client.get(f"/api/data/backups/{filename}")
    assert download.status_code == 200

    with zipfile.ZipFile(BytesIO(download.content)) as archive:
        names = archive.namelist()
        assert "manifest.json" in names
        assert "database/capstone.db" in names
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["backup_version"] == "1.0"
        assert any(item["path"] == "database/capstone.db" for item in manifest["files"])
        with tempfile.TemporaryDirectory() as temporary:
            restored = Path(temporary) / "capstone.db"
            restored.write_bytes(archive.read("database/capstone.db"))
            connection = sqlite3.connect(restored)
            try:
                assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
                name = connection.execute("SELECT name FROM career_profiles").fetchone()[0]
                assert name == "Recoverable Professional"
            finally:
                connection.close()
