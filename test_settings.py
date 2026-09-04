from settings import Settings, get_settings
from functools import lru_cache

import pytest
from pydantic import ValidationError

def test_settings_reads_application_environment(
        monkeypatch
):
    monkeypatch.setenv("DB_HOST", "database")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv(
        "DB_NAME",
        "game_player_service_test"
    )
    monkeypatch.setenv("DB_USER", "postgres")
    monkeypatch.setenv("DB_PASSWORD", "secret")
    monkeypatch.setenv("REDIS_HOST", "cache")
    monkeypatch.setenv("REDIS_PORT", "6379")
    monkeypatch.setenv(
        "RANKING_CACHE_TTL_SECONDS",
        "60"
    )
    monkeypatch.setenv(
        "REDIS_TIMEOUT_SECONDS",
        "0.5"
    )

    settings = Settings(_env_file=None)

    assert settings.db_host == "database"
    assert settings.db_port == 5432
    assert isinstance(settings.db_port, int)
    assert (
        settings.db_name
        == "game_player_service_test"
    )
    assert settings.db_user == "postgres"
    assert (
        settings.db_password.get_secret_value()
        == "secret"
    )
    assert settings.redis_host == "cache"
    assert settings.redis_port == 6379
    assert isinstance(settings.redis_port, int)
    assert settings.ranking_cache_ttl_seconds == 60
    assert settings.redis_timeout_seconds == 0.5
    assert isinstance(
        settings.redis_timeout_seconds,
        float
    )


@pytest.mark.parametrize(
    "db_port",
    [
        "0",
        "65536"
    ]
)
def test_settings_rejects_out_of_range_port(
        monkeypatch,
        db_port
):
    monkeypatch.setenv("DB_HOST", "database")
    monkeypatch.setenv("DB_PORT", db_port)
    monkeypatch.setenv("DB_NAME", "test_database")
    monkeypatch.setenv("DB_USER", "postgres")
    monkeypatch.setenv("DB_PASSWORD", "secret")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_settings_hides_database_password():
    settings = Settings(
        db_host="database",
        db_port=5432,
        db_name="test_database",
        db_user="postgres",
        db_password="very-secret-password",
        _env_file=None
    )

    assert (
        "very-secret-password"
        not in repr(settings)
    )


def test_get_settings_reuses_cached_instance(
        monkeypatch
):
    monkeypatch.setenv("DB_HOST", "database")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "test_database")
    monkeypatch.setenv("DB_USER", "postgres")
    monkeypatch.setenv("DB_PASSWORD", "secret")

    get_settings.cache_clear()

    try:
        first_settings = get_settings()
        second_settings = get_settings()

        assert first_settings is second_settings
    finally:
        get_settings.cache_clear()


def test_settings_rejects_missing_database_configuration(
        monkeypatch
):
    variable_names = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD"
    ]

    for variable_name in variable_names:
        monkeypatch.delenv(
            variable_name,
            raising=False
        )

    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None)

    missing_fields = {
        item["loc"][0]
        for item in error.value.errors()
    }

    assert missing_fields == {
        "db_host",
        "db_port",
        "db_name",
        "db_user",
        "db_password"
    }


def test_environment_variable_overrides_env_file(
        monkeypatch,
        tmp_path
):
    variable_names = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD"
    ]

    for variable_name in variable_names:
        monkeypatch.delenv(
            variable_name,
            raising=False
        )

    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join([
            "DB_HOST=file-database",
            "DB_PORT=5432",
            "DB_NAME=from_file",
            "DB_USER=postgres",
            "DB_PASSWORD=secret"
        ]),
        encoding="utf-8"
    )

    monkeypatch.setenv(
        "DB_NAME",
        "from_environment"
    )

    settings = Settings(
        _env_file=env_file
    )

    assert settings.db_host == "file-database"
    assert settings.db_name == "from_environment"
