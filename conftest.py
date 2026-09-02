import pytest

from database import get_connection
from settings import get_settings


from pathlib import Path

from alembic import command
from alembic.config import Config


BASE_DIR = Path(__file__).resolve().parent
TEST_DATABASE = "game_player_service_test"


@pytest.fixture(scope="session")
def migrated_test_database():
    environment = pytest.MonkeyPatch()
    environment.setenv("DB_NAME", TEST_DATABASE)
    get_settings.cache_clear()

    try:
        alembic_config = Config(
            str(BASE_DIR / "alembic.ini")
        )
        command.upgrade(alembic_config, "head")
    finally:
        get_settings.cache_clear()
        environment.undo()


@pytest.fixture
def reset_test_database(
        monkeypatch,
        migrated_test_database
):
    monkeypatch.setenv("DB_NAME", TEST_DATABASE)
    get_settings.cache_clear()

    try:
        with get_connection() as connection:
            assert (
                connection.info.dbname
                == TEST_DATABASE
            )

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    TRUNCATE TABLE
                        transfer_history,
                        players
                    RESTART IDENTITY
                    """
                )
                cursor.execute(
                    """
                    INSERT INTO players (name, score)
                    VALUES (%s, %s)
                    """,
                    ("Alice", 90)
                )

        yield

        with get_connection() as connection:
            assert (
                connection.info.dbname
                == TEST_DATABASE
            )

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    TRUNCATE TABLE
                        transfer_history,
                        players
                    RESTART IDENTITY
                    """
                )
    finally:
        get_settings.cache_clear()