from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from app.core.config import get_settings


def test_all_migrations_upgrade_an_empty_database_to_head(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database_path = tmp_path / "migration-test.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("CAPSTONE_DATABASE_URL", database_url)
    get_settings.cache_clear()
    project_root = Path(__file__).resolve().parents[1]
    config = Config(str(project_root / "alembic.ini"))
    config.set_main_option("script_location", str(project_root / "migrations"))
    config.set_main_option("sqlalchemy.url", database_url)

    command.upgrade(config, "head")

    engine = create_engine(database_url)
    with engine.connect() as connection:
        assert connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == (
            "20260730_0013"
        )
        assert connection.execute(text("PRAGMA integrity_check")).scalar_one() == "ok"
    tables = set(inspect(engine).get_table_names())
    assert {
        "career_assets",
        "documents",
        "strategic_goals",
        "targets",
        "opportunities",
        "job_applications",
        "career_documents",
        "fellowships",
        "award_pathways",
        "audit_events",
    }.issubset(tables)
    engine.dispose()
    get_settings.cache_clear()
