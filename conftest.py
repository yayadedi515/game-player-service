import pytest

from database import get_connection


TEST_DATABASE = "game_player_service_test"


@pytest.fixture
def reset_test_database(monkeypatch):
    monkeypatch.setenv("DB_NAME", TEST_DATABASE)

    with get_connection() as connection:
        assert connection.info.dbname == TEST_DATABASE

        with connection.cursor() as cursor:
            cursor.execute(
                "TRUNCATE TABLE transfer_history, players RESTART IDENTITY"
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
        assert connection.info.dbname == TEST_DATABASE

        with connection.cursor() as cursor:
            cursor.execute(
                "TRUNCATE TABLE transfer_history, players RESTART IDENTITY"
            )
