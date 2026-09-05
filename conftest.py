import pytest

from database import get_connection
from settings import get_settings
from redis import Redis


from pathlib import Path


from alembic import command
from alembic.config import Config
from ranking_cache import RedisRankingCache


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


@pytest.fixture(autouse=True)
def provide_test_jwt_secret(monkeypatch):
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-only-jwt-secret-key-123456789"
    )
    get_settings.cache_clear()

    yield

    get_settings.cache_clear()


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
                        players,
                        users
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
                        players,
                        users
                    RESTART IDENTITY
                    """
                )
    finally:
        get_settings.cache_clear()


@pytest.fixture
def reset_ranking_cache():
    settings = get_settings()
    redis_client = Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        decode_responses=True
    )

    redis_client.delete(
        RedisRankingCache.CACHE_KEY
    )

    try:
        yield
    finally:
        redis_client.delete(
            RedisRankingCache.CACHE_KEY
        )
        redis_client.close()
