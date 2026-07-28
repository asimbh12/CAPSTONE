import hashlib
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlmodel import Session, select

from app.core.config import get_settings
from app.models.career import AiHandlingPolicy, AiOperation, AuditEvent, Document, IngestionRun
from app.schemas.system import SystemCheck, SystemReadiness
from app.services.data_management import verify_backup


def _check(
    key: str,
    label: str,
    status: Literal["pass", "warning", "fail"],
    message: str,
    details: list[str] | None = None,
) -> SystemCheck:
    return SystemCheck(
        key=key,
        label=label,
        status=status,
        message=message,
        details=details or [],
    )


def _migration_heads() -> set[str]:
    project_root = Path(__file__).resolve().parents[2]
    config = Config(str(project_root / "alembic.ini"))
    config.set_main_option("script_location", str(project_root / "migrations"))
    return set(ScriptDirectory.from_config(config).get_heads())


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_system_readiness(session: Session) -> SystemReadiness:
    settings = get_settings()
    checks: list[SystemCheck] = []

    database_result = str(session.execute(text("PRAGMA quick_check")).scalar_one())
    checks.append(
        _check(
            "database_integrity",
            "SQLite integrity",
            "pass" if database_result == "ok" else "fail",
            "SQLite quick check passed."
            if database_result == "ok"
            else f"SQLite quick check returned: {database_result}",
        )
    )

    expected_heads = _migration_heads()
    try:
        current_revisions = {
            str(row[0])
            for row in session.execute(text("SELECT version_num FROM alembic_version")).all()
        }
    except Exception:
        current_revisions = set()
    migrations_current = current_revisions == expected_heads
    checks.append(
        _check(
            "database_migrations",
            "Database migrations",
            "pass" if migrations_current else "fail",
            "Database schema is at the current migration head."
            if migrations_current
            else "Database schema revision does not match the application.",
            [] if migrations_current else [
                f"Current: {', '.join(sorted(current_revisions)) or 'not recorded'}",
                f"Expected: {', '.join(sorted(expected_heads))}",
            ],
        )
    )

    storage_error = ""
    try:
        settings.data_root.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=settings.data_root, delete=True):
            pass
    except OSError as exc:
        storage_error = str(exc)
    checks.append(
        _check(
            "local_storage",
            "Local storage",
            "fail" if storage_error else "pass",
            f"Local data storage is not writable: {storage_error}"
            if storage_error
            else "Local data storage is writable.",
        )
    )

    missing_documents: list[str] = []
    changed_documents: list[str] = []
    invalid_paths: list[str] = []
    root = settings.data_root.resolve()
    documents = list(session.exec(select(Document)).all())
    for document in documents:
        path = (root / document.relative_path).resolve()
        if root not in path.parents:
            invalid_paths.append(document.original_filename)
        elif not path.is_file():
            missing_documents.append(document.original_filename)
        elif _file_sha256(path) != document.sha256:
            changed_documents.append(document.original_filename)
    document_failures = invalid_paths + missing_documents + changed_documents
    checks.append(
        _check(
            "document_integrity",
            "Stored document integrity",
            "fail" if document_failures else "pass",
            f"{len(document_failures)} stored document integrity problem(s) detected."
            if document_failures
            else f"All {len(documents)} stored document(s) match their recorded checksums.",
            [
                *[f"Invalid path: {item}" for item in invalid_paths],
                *[f"Missing: {item}" for item in missing_documents],
                *[f"Checksum mismatch: {item}" for item in changed_documents],
            ][:20],
        )
    )

    valid_policies = {item.value for item in AiHandlingPolicy}
    invalid_policy_runs = [
        str(run.id)
        for run in session.exec(select(IngestionRun)).all()
        if run.ai_handling_policy not in valid_policies
    ]
    invalid_policy_documents = [
        document.original_filename
        for document in documents
        if document.ai_handling_policy not in valid_policies
    ]
    runs_by_id = {
        str(run.id): run for run in session.exec(select(IngestionRun)).all()
    }
    external_policy_violations = [
        operation.entity_id
        for operation in session.exec(select(AiOperation)).all()
        if operation.provider.casefold() not in {"deterministic", "local"}
        and operation.entity_type == "ingestion_run"
        and operation.entity_id in runs_by_id
        and runs_by_id[operation.entity_id].ai_handling_policy
        != AiHandlingPolicy.AI_ALLOWED.value
    ]
    policy_failures = (
        invalid_policy_runs + invalid_policy_documents + external_policy_violations
    )
    checks.append(
        _check(
            "ai_data_policy",
            "AI handling policy",
            "fail" if policy_failures else "pass",
            "AI handling policies are valid and no local-only source has an external AI operation."
            if not policy_failures
            else f"{len(policy_failures)} AI handling policy problem(s) detected.",
            [
                *[f"Invalid ingestion policy: {item}" for item in invalid_policy_runs],
                *[f"Invalid document policy: {item}" for item in invalid_policy_documents],
                *[
                    f"External AI used for restricted ingestion: {item}"
                    for item in external_policy_violations
                ],
            ][:20],
        )
    )

    backup_dir = settings.data_root / "backups"
    backups = sorted(
        backup_dir.glob("capstone-backup-*.zip"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    ) if backup_dir.exists() else []
    if not backups:
        checks.append(
            _check(
                "recoverable_backup",
                "Recoverable backup",
                "warning",
                "No local backup is available. Create and download a verified backup.",
            )
        )
    else:
        latest = backups[0]
        verification = verify_backup(latest)
        age = datetime.now(UTC) - datetime.fromtimestamp(latest.stat().st_mtime, tz=UTC)
        if not verification.valid:
            checks.append(
                _check(
                    "recoverable_backup",
                    "Recoverable backup",
                    "fail",
                    "The latest backup failed verification.",
                    verification.errors[:20],
                )
            )
        elif age > timedelta(days=7):
            checks.append(
                _check(
                    "recoverable_backup",
                    "Recoverable backup",
                    "warning",
                    f"The latest verified backup is {age.days} days old.",
                )
            )
        else:
            checks.append(
                _check(
                    "recoverable_backup",
                    "Recoverable backup",
                    "pass",
                    f"Latest backup is verified ({verification.file_count} files).",
                )
            )

    failed_runs = list(
        session.exec(select(IngestionRun).where(IngestionRun.status == "failed")).all()
    )
    checks.append(
        _check(
            "failed_operations",
            "Recoverable workflow failures",
            "warning" if failed_runs else "pass",
            f"{len(failed_runs)} failed ingestion(s) require review."
            if failed_runs
            else "No failed ingestion workflows require attention.",
            [run.source_label for run in failed_runs[:20]],
        )
    )

    audit_count = len(list(session.exec(select(AuditEvent.id)).all()))
    checks.append(
        _check(
            "audit_history",
            "Audit history",
            "pass" if audit_count else "warning",
            f"{audit_count} audit event(s) are available."
            if audit_count
            else "No audit events exist yet.",
        )
    )

    failures = sum(item.status == "fail" for item in checks)
    warnings = sum(item.status == "warning" for item in checks)
    passed = sum(item.status == "pass" for item in checks)
    status: Literal["ready", "attention", "blocked"] = (
        "blocked" if failures else "attention" if warnings else "ready"
    )
    return SystemReadiness(
        status=status,
        checked_at=datetime.now(UTC),
        passed=passed,
        warnings=warnings,
        failures=failures,
        checks=checks,
    )
