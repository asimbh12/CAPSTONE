from app.core.config import Settings


def test_cors_origins_accept_comma_separated_environment_value() -> None:
    settings = Settings(cors_origins="http://localhost:5173,http://127.0.0.1:5173")  # type: ignore[arg-type]

    assert settings.cors_origins == ["http://localhost:5173", "http://127.0.0.1:5173"]
