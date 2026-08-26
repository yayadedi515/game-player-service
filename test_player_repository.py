from multiprocessing import connection

import pytest

from database import get_connection
from player_repository import create_player, find_player_by_name



TEST_DATABASE = "game_player_service_test"
pytestmark = pytest.mark.integration

@pytest.fixture(autouse=True)
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


def test_find_existing_player():
    player = find_player_by_name("Alice")

    assert player["player_id"] == 1
    assert player["name"] == "Alice"
    assert player["score"] == 90
    assert player["created_at"] is not None


def test_find_spaced_player():
    player = find_player_by_name("          Alice       ")

    assert player["player_id"] == 1
    assert player["name"] == "Alice"
    assert player["score"] == 90
    assert player["created_at"] is not None


def test_find_player_not_exists():
    player = find_player_by_name("Aooshiro9")

    assert player is None


def test_find_player_all_space():
    players = find_player_by_name("   ")

    assert players is None


def test_find_player_with_sql_inject():
    player = find_player_by_name("Alice' OR '1' = '1' --")

    assert player is None


def test_create_player():
    player = create_player('Diana')

    assert player["player_id"] == 2
    assert player["name"] == "Diana"
    assert player["score"] == 0
    assert player["created_at"] is not None

    result = find_player_by_name("Diana")

    assert result == player

def test_create_duplicate_player_returns_none():
    player = create_player("Alice")

    assert player is None

def test_create_player_strips_whitespace():
    player = create_player("    Diana  ")

    assert player["name"] == "Diana"
    assert player["player_id"] == 2
    assert player["score"] == 0

    result = find_player_by_name("Diana")
    assert result == player


def test_create_blank_player_returns_none():
    player = create_player("        ")

    assert player is None

    query = """
        SELECT COUNT(*) FROM players
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()

    assert row[0] == 1