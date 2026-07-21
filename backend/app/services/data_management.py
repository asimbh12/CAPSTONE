import hashlib
import json
import sqlite3
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import ValidationError
from sqlalchemy.engine import make_url
from sqlmodel import Session, col, select

from app.core.config import get_settings
from app.models.career import (
    CareerAsset,
    CareerProfile,
    Document,
    EvidenceItem,
    Organisation,
    Person,
    StrategicGoal,
    Theme,
)
from app.schemas.career import (
    AssetCreate,
    GoalCreate,
    ImportReport,
    OrganisationCreate,
    PersonCreate,
    ProfileInput,
    ThemeCreate,
)
from app.services.audit import record_audit
from app.services.career import build_asset_read, create_asset

SCHEMA_VERSION = "1.0"


def build_export(session: Session) -> dict[str, Any]:
    profile = session.exec(select(CareerProfile).limit(1)).first()
    themes = session.exec(select(Theme).order_by(col(Theme.name))).all()
    goals = session.exec(select(StrategicGoal).order_by(col(StrategicGoal.created_at))).all()
    organisations = session.exec(select(Organisation).order_by(col(Organisation.name))).all()
    people = session.exec(select(Person).order_by(col(Person.name))).all()
    assets = session.exec(select(CareerAsset).order_by(col(CareerAsset.created_at))).all()
    documents = session.exec(select(Document).order_by(col(Document.created_at))).all()
    evidence = session.exec(select(EvidenceItem).order_by(col(EvidenceItem.created_at))).all()
    return cast(
        dict[str, Any],
        jsonable_encoder(
            {
                "schema_version": SCHEMA_VERSION,
                "exported_at": datetime.now(UTC),
                "profile": profile,
                "themes": themes,
                "goals": goals,
                "organisations": organisations,
                "people": people,
                "assets": [build_asset_read(session, asset) for asset in assets],
                "documents": documents,
                "evidence": evidence,
            }
        ),
    )


def _records(payload: dict[str, object], key: str) -> list[dict[str, Any]]:
    value = payload.get(key, [])
    if not isinstance(value, list):
        raise ValueError(f"{key} must be an array")
    if not all(isinstance(item, dict) for item in value):
        raise ValueError(f"Every {key} entry must be an object")
    return value


def import_data(session: Session, payload: dict[str, object], *, mode: str) -> ImportReport:
    errors: list[str] = []
    warnings: list[str] = []
    schema_version = str(payload.get("schema_version", ""))
    if schema_version != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")

    try:
        profile_raw = payload.get("profile")
        profile = (
            ProfileInput.model_validate(profile_raw) if isinstance(profile_raw, dict) else None
        )
        theme_inputs = [ThemeCreate.model_validate(item) for item in _records(payload, "themes")]
        goal_inputs = [GoalCreate.model_validate(item) for item in _records(payload, "goals")]
        organisation_inputs = [
            OrganisationCreate.model_validate(item) for item in _records(payload, "organisations")
        ]
        person_inputs = [PersonCreate.model_validate(item) for item in _records(payload, "people")]
        asset_inputs = [AssetCreate.model_validate(item) for item in _records(payload, "assets")]
    except (ValidationError, ValueError) as exc:
        errors.append(str(exc))
        profile = None
        theme_inputs = []
        goal_inputs = []
        organisation_inputs = []
        person_inputs = []
        asset_inputs = []

    existing_titles = set(session.exec(select(CareerAsset.title)).all())
    duplicate_titles = sorted(
        {item.title for item in asset_inputs if item.title in existing_titles}
    )
    if duplicate_titles:
        warnings.append("Assets with duplicate titles will be skipped")

    counts = {
        "profiles": 1 if profile else 0,
        "themes": len(theme_inputs),
        "goals": len(goal_inputs),
        "organisations": len(organisation_inputs),
        "people": len(person_inputs),
        "assets": len(asset_inputs),
    }
    valid = not errors
    applied = False
    if mode == "apply" and valid:
        existing_profile = session.exec(select(CareerProfile).limit(1)).first()
        if profile:
            target = existing_profile or CareerProfile()
            for key, value in profile.model_dump().items():
                setattr(target, key, value)
            target.updated_at = datetime.now(UTC)
            session.add(target)

        existing_theme_names = set(session.exec(select(Theme.name)).all())
        for theme_input in theme_inputs:
            if theme_input.name not in existing_theme_names:
                session.add(Theme(**theme_input.model_dump(), provenance="import"))
                existing_theme_names.add(theme_input.name)

        existing_org_names = set(session.exec(select(Organisation.name)).all())
        for organisation_input in organisation_inputs:
            if organisation_input.name not in existing_org_names:
                session.add(Organisation(**organisation_input.model_dump(), provenance="import"))
                existing_org_names.add(organisation_input.name)

        for goal_input in goal_inputs:
            session.add(StrategicGoal(**goal_input.model_dump(), provenance="import"))
        for person_input in person_inputs:
            # Cross-import ID mapping is deliberately deferred; invalid external IDs are cleared.
            values = person_input.model_dump()
            values["organisation_id"] = None
            session.add(Person(**values, provenance="import"))
        session.flush()
        for asset_input in asset_inputs:
            if asset_input.title not in existing_titles:
                safe_item = asset_input.model_copy(
                    update={"organisation_id": None, "theme_ids": []}
                )
                create_asset(session, safe_item, source="import")
                existing_titles.add(asset_input.title)
        record_audit(
            session,
            entity_type="data_import",
            entity_id=datetime.now(UTC).isoformat(),
            action="applied",
            source="import",
            details=counts,
        )
        session.commit()
        applied = True

    return ImportReport(
        mode=mode,
        schema_version=schema_version,
        valid=valid,
        counts=counts,
        errors=errors,
        warnings=warnings,
        duplicate_titles=duplicate_titles,
        applied=applied,
    )


def _sqlite_database_path() -> Path:
    url = make_url(get_settings().database_url)
    if url.get_backend_name() != "sqlite" or not url.database:
        raise HTTPException(status_code=501, detail="Local backup currently supports SQLite only")
    return Path(url.database).resolve()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_backup(session: Session) -> Path:
    settings = get_settings()
    backup_dir = settings.data_root / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    destination = backup_dir / f"capstone-backup-{timestamp}.zip"
    source_database = _sqlite_database_path()
    if not source_database.exists():
        raise HTTPException(status_code=500, detail="SQLite database file is missing")

    with tempfile.TemporaryDirectory() as temporary:
        snapshot = Path(temporary) / "capstone.db"
        source = sqlite3.connect(source_database)
        target = sqlite3.connect(snapshot)
        try:
            source.backup(target)
        finally:
            target.close()
            source.close()
        files: list[tuple[Path, str]] = [(snapshot, "database/capstone.db")]
        for directory_name in ("originals", "derived", "generated"):
            directory = settings.data_root / directory_name
            if directory.exists():
                files.extend(
                    (path, path.relative_to(settings.data_root).as_posix())
                    for path in directory.rglob("*")
                    if path.is_file()
                )
        manifest = {
            "backup_version": "1.0",
            "created_at": datetime.now(UTC).isoformat(),
            "files": [
                {"path": archive_name, "sha256": _sha256(path), "byte_size": path.stat().st_size}
                for path, archive_name in files
            ],
        }
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", json.dumps(manifest, indent=2))
            for path, archive_name in files:
                archive.write(path, archive_name)

    record_audit(
        session,
        entity_type="backup",
        entity_id=destination.name,
        action="created",
        details={"byte_size": destination.stat().st_size},
    )
    session.commit()
    return destination


def resolve_backup(filename: str) -> Path:
    if Path(filename).name != filename or not filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Invalid backup filename")
    root = (get_settings().data_root / "backups").resolve()
    path = (root / filename).resolve()
    if root not in path.parents or not path.is_file():
        raise HTTPException(status_code=404, detail="Backup not found")
    return path
