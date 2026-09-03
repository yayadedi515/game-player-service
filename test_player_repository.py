import pytest
from psycopg.errors import (
    ForeignKeyViolation,
    NumericValueOutOfRange,
    RestrictViolation,
)

from database import get_connection
from player_repository import PlayerRepository
from transfer_result import TransferResult

pytestmark = [
    pytest.mark.integration,
    pytest.mark.usefixtures("reset_test_database")
]

repository = PlayerRepository()

def test_find_existing_player():
    player = repository.find_player_by_name("Alice")

    assert player["player_id"] == 1
    assert player["name"] == "Alice"
    assert player["score"] == 90
    assert player["created_at"] is not None


def test_find_spaced_player():
    player = repository.find_player_by_name("          Alice       ")

    assert player["player_id"] == 1
    assert player["name"] == "Alice"
    assert player["score"] == 90
    assert player["created_at"] is not None


def test_find_player_not_exists():
    player = repository.find_player_by_name("Aooshiro9")

    assert player is None


def test_find_player_all_space():
    players = repository.find_player_by_name("   ")

    assert players is None


def test_find_player_with_sql_inject():
    player = repository.find_player_by_name("Alice' OR '1' = '1' --")

    assert player is None


def test_create_player():
    player = repository.create_player('Diana')

    assert player["player_id"] == 2
    assert player["name"] == "Diana"
    assert player["score"] == 0
    assert player["created_at"] is not None

    result = repository.find_player_by_name("Diana")

    assert result == player


def test_create_duplicate_player_returns_none():
    player = repository.create_player("Alice")

    assert player is None


def test_create_player_strips_whitespace():
    player = repository.create_player("    Diana  ")

    assert player["name"] == "Diana"
    assert player["player_id"] == 2
    assert player["score"] == 0

    result = repository.find_player_by_name("Diana")
    assert result == player


def test_create_blank_player_returns_none():
    player = repository.create_player("        ")

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
    player = repository.add_score('Alice', 30)
    assert player is not None
    assert player["player_id"] == 1
    assert player["name"] == "Alice"
    assert player["score"] == 120
    assert player["created_at"] is not None

    result = repository.find_player_by_name("Alice")

    assert result == player


def test_add_score_rejects_negative_points():
    player = repository.add_score("Alice", -10)

    assert player is None

    result = repository.find_player_by_name("Alice")
    assert result["score"] == 90


def test_add_score_strips_whitespace():
    player = repository.add_score("  Alice  ", 30)
    assert player is not None
    assert player["name"] == "Alice"
    assert player["score"] == 120

    result = repository.find_player_by_name("Alice")
    assert result["score"] == player["score"]


def test_add_score_missing_player_returns_none():
    player = repository.add_score("Cindy", 30)

    assert player is None
    result = repository.find_player_by_name("Alice")
    assert result["score"] == 90


def test_add_score_blank_name_returns_none():
    player = repository.add_score("        ", 30)

    assert player is None
    result = repository.find_player_by_name("Alice")
    assert result["score"] == 90


def test_add_score_zero_points():
    player = repository.add_score("Alice", 0)

    assert player is not None
    assert player["score"] == 90

    result = repository.find_player_by_name("Alice")
    assert result == player


def test_get_ranking_orders_by_score_and_name():
    repository.create_player("Bob")
    repository.create_player("Charlie")
    repository.create_player("Diana")
    repository.add_score("Bob", 90)
    repository.add_score("Charlie", 90)
    repository.add_score("Diana", 120)

    ranking = repository.get_ranking()

    assert [player["name"] for player in ranking] == [
        "Diana", "Alice", "Bob", "Charlie"
    ]
    assert [player["score"] for player in ranking] == [
        120, 90, 90, 90
    ]
    assert ranking == [
        repository.find_player_by_name("Diana"),
        repository.find_player_by_name("Alice"),
        repository.find_player_by_name("Bob"),
        repository.find_player_by_name("Charlie"),
    ]


def test_get_ranking_empty_table_returns_empty_list():
    query = """
        DELETE FROM players
    """
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)

    result = repository.get_ranking()

    assert result == []


def test_transfer_score_updates_both_players_and_records_history():
    alice = repository.find_player_by_name("Alice")
    bob = repository.create_player("Bob")

    assert alice is not None
    assert bob is not None

    success = repository.transfer_score("Alice", "Bob", 30)

    assert success is TransferResult.SUCCESS

    player_alice = repository.find_player_by_name("Alice")
    player_bob = repository.find_player_by_name("Bob")

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


def test_transfer_score_missing_receiver_returns_player_not_found():
    result = repository.transfer_score("Alice", "Cindy", 30)
    assert result is TransferResult.PLAYER_NOT_FOUND

    player = repository.find_player_by_name("Alice")
    assert player["score"] == 90

    query = """
        SELECT COUNT(*) FROM transfer_history
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()

    assert row[0] == 0


def test_transfer_score_insufficient_balance_returns_insufficient_score():
    repository.create_player("Bob")

    result = repository.transfer_score("Alice", "Bob", 150)

    assert result is TransferResult.INSUFFICIENT_SCORE

    alice = repository.find_player_by_name("Alice")
    bob = repository.find_player_by_name("Bob")

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
        (-1, TransferResult.INVALID_REQUEST, 90, 0, 0),
        (0, TransferResult.INVALID_REQUEST, 90, 0, 0),
        (1, TransferResult.SUCCESS, 89, 1, 1),
        (89, TransferResult.SUCCESS, 1, 89, 1),
        (90, TransferResult.SUCCESS, 0, 90, 1),
        (91, TransferResult.INSUFFICIENT_SCORE, 90, 0, 0),
    ],
)
def test_transfer_score_points_boundaries(
        points,
        expected_result,
        expected_alice_score,
        expected_bob_score,
        expected_history_count,
):
    repository.create_player("Bob")

    result = repository.transfer_score("Alice", "Bob", points)

    assert result is expected_result

    alice = repository.find_player_by_name("Alice")
    bob = repository.find_player_by_name("Bob")

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
    (
        "sender_name",
        "receiver_name",
        "expected_result",
    ),
    [
        (
            "        ",
            "Bob",
            TransferResult.INVALID_REQUEST,
        ),
        (
            "Alice",
            "        ",
            TransferResult.INVALID_REQUEST,
        ),
        (
            "Alice",
            "Alice",
            TransferResult.INVALID_REQUEST,
        ),
        (
            "Cindy",
            "Bob",
            TransferResult.PLAYER_NOT_FOUND,
        ),
    ],
)
def test_transfer_score_rejects_invalid_players_without_changes(
        sender_name,
        receiver_name,
        expected_result,
):
    repository.create_player("Bob")

    result = repository.transfer_score(sender_name, receiver_name, 30)

    assert result is expected_result

    alice = repository.find_player_by_name("Alice")
    bob = repository.find_player_by_name("Bob")

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
    repository.create_player("Bob")

    result = repository.transfer_score(" Alice ", " Bob ", 30)

    assert result is TransferResult.SUCCESS
    alice = repository.find_player_by_name("Alice")
    bob = repository.find_player_by_name("Bob")
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


def test_transfer_score_rolls_back_when_receiver_update_fails():
    repository.create_player("Bob")
    repository.add_score("Bob", 2_147_483_647)

    with pytest.raises(NumericValueOutOfRange):
        repository.transfer_score("Alice", "Bob", 1)

    alice = repository.find_player_by_name("Alice")
    bob = repository.find_player_by_name("Bob")

    assert alice is not None
    assert bob is not None
    assert alice["score"] == 90
    assert bob["score"] == 2_147_483_647

    query = """
        SELECT COUNT(*) FROM transfer_history
    """

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            row = cursor.fetchone()

    assert row[0] == 0


def test_delete_existing_player():
    player = repository.delete_player("Alice")
    assert player["player_id"] == 1
    assert player["name"] == "Alice"
    assert player["score"] == 90
    assert player["created_at"] is not None

    result = repository.find_player_by_name("Alice")
    assert result is None


def test_delete_missing_player_returns_none():
    player = repository.delete_player("Bob")

    assert player is None

    result = repository.find_player_by_name("Alice")

    assert result is not None


def test_delete_player_strips_whitespace():
    player = repository.delete_player("  Alice  ")

    assert player["name"] == "Alice"

    result = repository.find_player_by_name("Alice")

    assert result is None


def test_delete_blank_player_returns_none():
    player = repository.delete_player("    ")

    assert player is None

    result = repository.find_player_by_name("Alice")

    assert result is not None


def test_delete_player_with_transfer_history_raises_reference_violation():
    repository.create_player("Bob")
    success = repository.transfer_score("Alice", "Bob", 10)

    assert success is TransferResult.SUCCESS

    with pytest.raises(
        (ForeignKeyViolation, RestrictViolation)
    ):
        repository.delete_player("Alice")

    result = repository.find_player_by_name("Alice")

    assert result is not None
    assert result["score"] == 80


def test_get_transfer_history_returns_transfer():
    repository.create_player("Bob")

    result = repository.transfer_score(
        "Alice",
        "Bob",
        30
    )
    assert result is TransferResult.SUCCESS

    history = repository.get_transfer_history()

    assert len(history) == 1
    assert history[0]["transfer_id"] == 1
    assert history[0]["sender"] == "Alice"
    assert history[0]["receiver"] == "Bob"
    assert history[0]["points"] == 30
    assert history[0]["created_at"] is not None


def test_get_transfer_history_empty_returns_empty_list():
    history = repository.get_transfer_history()

    assert history == []


def test_get_transfer_history_orders_newest_first():
    repository.create_player("Bob")

    first_result = repository.transfer_score(
        "Alice",
        "Bob",
        30
    )
    second_result = repository.transfer_score(
        "Bob",
        "Alice",
        10
    )

    assert first_result is TransferResult.SUCCESS
    assert second_result is TransferResult.SUCCESS

    history = repository.get_transfer_history()

    assert len(history) == 2

    assert history[0]["transfer_id"] == 2
    assert history[0]["sender"] == "Bob"
    assert history[0]["receiver"] == "Alice"
    assert history[0]["points"] == 10

    assert history[1]["transfer_id"] == 1
    assert history[1]["sender"] == "Alice"
    assert history[1]["receiver"] == "Bob"
    assert history[1]["points"] == 30


def test_get_transfer_history_supports_pagination():
    repository.create_player("Bob")

    results = [
        repository.transfer_score("Alice", "Bob", 30),
        repository.transfer_score("Bob", "Alice", 10),
        repository.transfer_score("Alice", "Bob", 20),
    ]

    assert results == [
        TransferResult.SUCCESS,
        TransferResult.SUCCESS,
        TransferResult.SUCCESS,
    ]

    history = repository.get_transfer_history(
        limit=1,
        offset=1
    )

    assert len(history) == 1
    assert history[0]["transfer_id"] == 2
    assert history[0]["sender"] == "Bob"
    assert history[0]["receiver"] == "Alice"
    assert history[0]["points"] == 10


@pytest.mark.parametrize(
    ("limit", "offset"),
    [
        (0, 0),
        (101, 0),
        (20, -1),
    ],
)
def test_get_transfer_history_rejects_invalid_pagination(
        limit,
        offset
):
    with pytest.raises(
        ValueError,
        match="Invalid pagination parameters"
    ):
        repository.get_transfer_history(
            limit=limit,
            offset=offset
        )
