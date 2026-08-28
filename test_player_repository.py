from multiprocessing import connection

import pytest

from database import get_connection
from player_repository import (
    create_player,
    find_player_by_name,
    add_score,
    get_ranking,
    transfer_score
)



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


def test_add_score_updates_and_returns_player():
    player = add_score('Alice', 30)
    assert player is not None
    assert player["player_id"] == 1
    assert player["name"] == "Alice"
    assert player["score"] == 120
    assert player["created_at"] is not None

    result = find_player_by_name("Alice")

    assert result == player


def test_add_score_rejects_negative_points():
    player = add_score("Alice", -10)

    assert player is None

    result = find_player_by_name("Alice")
    assert result["score"] == 90


def test_add_score_strips_whitespace():
    player = add_score("  Alice  ", 30)
    assert player is not None
    assert player["name"] == "Alice"
    assert player["score"] == 120

    result = find_player_by_name("Alice")
    assert result["score"] == player["score"]


def test_add_score_missing_player_returns_none():
    player = add_score("Cindy", 30)

    assert player is None
    result = find_player_by_name("Alice")
    assert result["score"] == 90


def test_add_score_blank_name_returns_none():
    player = add_score("        ", 30)

    assert player is None
    result = find_player_by_name("Alice")
    assert result["score"] == 90


def test_add_score_zero_points():
    player = add_score("Alice", 0)

    assert player is not None
    assert player["score"] == 90

    result = find_player_by_name("Alice")
    assert result == player


def test_get_ranking_orders_by_score_and_name():
    create_player("Bob")
    create_player("Charlie")
    create_player("Diana")
    add_score("Bob", 90)
    add_score("Charlie", 90)
    add_score("Diana", 120)

    ranking = get_ranking()

    assert [player["name"] for player in ranking] == [
        "Diana", "Alice", "Bob", "Charlie"
    ]
    assert [player["score"] for player in ranking] == [
        120, 90, 90, 90
    ]
    assert ranking == [
        find_player_by_name("Diana"),
        find_player_by_name("Alice"),
        find_player_by_name("Bob"),
        find_player_by_name("Charlie"),
    ]

def test_get_ranking_empty_table_returns_empty_list():
    query = """
        DELETE FROM players
    """
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)

    result = get_ranking()

    assert result == []


def test_transfer_score_updates_both_players_and_records_history():
    alice = find_player_by_name("Alice")
    bob = create_player("Bob")

    assert alice is not None
    assert bob is not None

    success = transfer_score("Alice", "Bob", 30)

    assert success is True

    player_alice = find_player_by_name("Alice")
    player_bob = find_player_by_name("Bob")

    assert player_alice["score"] == 60
    assert player_bob["score"] == 30

    query = """
        SELECT sender_id, receiver_id, points, created_at
        FROM transfer_history
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

    assert len(rows) == 1

    row = rows[0]
    assert row[0] == alice["player_id"]
    assert row[1] == bob["player_id"]
    assert row[2] == 30
    assert row[3] is not None


def test_transfer_score_missing_receiver_returns_false_without_changes():
    result = transfer_score("Alice", "Cindy", 30)
    assert result is False

    player = find_player_by_name("Alice")
    assert player["score"] == 90

    query = """
        SELECT COUNT(*) FROM transfer_history
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()

    assert row[0] == 0


def test_transfer_score_insufficient_balance_returns_false_without_changes():
    create_player("Bob")

    result = transfer_score("Alice", "Bob", 150)

    assert result is False

    alice = find_player_by_name("Alice")
    bob = find_player_by_name("Bob")

    assert alice is not None
    assert bob is not None
    assert alice["score"] == 90
    assert bob["score"] == 0

    query = """
        SELECT COUNT(*) FROM transfer_history
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()

    assert row[0] == 0


@pytest.mark.parametrize(
    (
        "points",
        "expected_result",
        "expected_alice_score",
        "expected_bob_score",
        "expected_history_count",
    ),
    [
        (-1, False, 90, 0, 0),
        (0, False, 90, 0, 0),
        (1, True, 89, 1, 1),
        (89, True, 1, 89, 1),
        (90, True, 0, 90, 1),
        (91, False, 90, 0, 0),
    ],
)
def test_transfer_score_points_boundaries(
    points,
    expected_result,
    expected_alice_score,
    expected_bob_score,
    expected_history_count,
):
    create_player("Bob")

    result = transfer_score("Alice", "Bob", points)

    assert result is expected_result

    alice = find_player_by_name("Alice")
    bob = find_player_by_name("Bob")

    assert alice["score"] == expected_alice_score
    assert bob["score"] == expected_bob_score

    query = """
        SELECT COUNT(*) FROM transfer_history
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()

    assert row[0] == expected_history_count


@pytest.mark.parametrize(
    ("sender_name", "receiver_name"),
    [
        ("        ", "Bob"),
        ("Alice", "        "),
        ("Alice", "Alice"),
        ("Cindy", "Bob"),
    ],
)
def test_transfer_score_rejects_invalid_players_without_changes(
    sender_name,
    receiver_name,
):
    create_player("Bob")

    result = transfer_score(sender_name, receiver_name, 30)

    assert result is False

    alice = find_player_by_name("Alice")
    bob = find_player_by_name("Bob")

    assert alice is not None
    assert bob is not None
    assert alice["score"] == 90
    assert bob["score"] == 0

    query = """
        SELECT COUNT(*) FROM transfer_history
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()

    assert row[0] == 0


def test_transfer_score_strips_whitespace():
    create_player("Bob")

    result = transfer_score(" Alice ", " Bob ", 30)

    assert result is True
    alice = find_player_by_name("Alice")
    bob = find_player_by_name("Bob")
    assert alice is not None
    assert bob is not None
    assert alice["score"] == 60
    assert bob["score"] == 30
    query = """
        SELECT COUNT(*) FROM transfer_history
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()

    assert row[0] == 1