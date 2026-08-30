import pytest
from fastapi.testclient import TestClient

from main import app
from player_repository import transfer_score
from transfer_result import TransferResult

pytestmark = [
    pytest.mark.integration,
    pytest.mark.usefixtures("reset_test_database")
]

client = TestClient(app)


def test_get_player_from_postgresql():
    response = client.get("/players/Alice")

    assert response.status_code == 200
    assert response.json() == {
        "name": "Alice",
        "score": 90
    }


def test_create_player_in_postgresql():
    response = client.post(
        "/players",
        json={"name": "Diana"}
    )

    assert response.status_code == 201
    assert response.json() == {
        "name": "Diana",
        "score": 0
    }

    saved_response = client.get("/players/Diana")

    assert saved_response.status_code == 200
    assert saved_response.json() == {
        "name": "Diana",
        "score": 0
    }


def test_get_ranking_from_postgresql():
    client.post(
        "/players",
        json={"name": "Charlie"}
    )
    client.post(
        "/players",
        json={"name": "Bob"}
    )

    response = client.get("/ranking")

    assert response.status_code == 200
    assert response.json() == {
        "ranking": [
    {
        "name": "Alice",
        "score": 90
    },
    {
        "name": "Bob",
        "score": 0
    },
    {
        "name": "Charlie",
        "score": 0
    }
    ]
    }


def test_delete_player_from_postgresql():
    response = client.delete("/players/Alice")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Alice has been deleted"
    }

    deleted_response = client.get("/players/Alice")

    assert deleted_response.status_code == 404
    assert deleted_response.json() == {
        "detail": "Player not found"
    }


def test_delete_player_with_transfer_history_returns_conflict_from_postgresql():
    create_response = client.post(
        "/players",
        json={"name": "Bob"}
    )
    assert create_response.status_code == 201

    success = transfer_score(
        "Alice",
        "Bob",
        10
    )
    assert success is TransferResult.SUCCESS

    response = client.delete("/players/Alice")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Player has transfer history"
    }

    existing_response = client.get("/players/Alice")

    assert existing_response.status_code == 200
    assert existing_response.json() == {
        "name": "Alice",
        "score": 80
    }


def test_add_score_persists_to_postgresql():
    response = client.patch(
        "/players/Alice/score",
        json={"points": 30}
    )

    assert response.status_code == 200
    assert response.json() == {
        "name": "Alice",
        "score": 120
    }

    get_response = client.get("/players/Alice")

    assert get_response.status_code == 200
    assert get_response.json() == {
        "name": "Alice",
        "score": 120
    }


def test_transfer_score_persists_to_postgresql():
    create_response = client.post(
        "/players",
        json={"name": "Bob"}
    )
    assert create_response.status_code == 201

    transfer_response = client.post(
        "/transfers",
        json={
            "sender": "Alice",
            "receiver": "Bob",
            "points": 30
        }
    )

    assert transfer_response.status_code == 201
    assert transfer_response.json() == {
        "sender": "Alice",
        "receiver": "Bob",
        "points": 30
    }

    alice_response = client.get("/players/Alice")
    bob_response = client.get("/players/Bob")

    assert alice_response.status_code == 200
    assert bob_response.status_code == 200

    assert alice_response.json() == {
        "name": "Alice",
        "score": 60
    }
    assert bob_response.json() == {
        "name": "Bob",
        "score": 30
    }


def test_transfer_score_insufficient_score_returns_conflict_from_postgresql():
    create_response = client.post(
        "/players",
        json={"name": "Bob"}
    )
    assert create_response.status_code == 201

    transfer_response = client.post(
        "/transfers",
        json={
            "sender": "Alice",
            "receiver": "Bob",
            "points": 91
        }
    )

    assert transfer_response.status_code == 409
    assert transfer_response.json() == {
        "detail": "Insufficient score"
    }

    alice_response = client.get("/players/Alice")
    bob_response = client.get("/players/Bob")

    assert alice_response.status_code == 200
    assert bob_response.status_code == 200

    assert alice_response.json() == {
        "name": "Alice",
        "score": 90
    }
    assert bob_response.json() == {
        "name": "Bob",
        "score": 0
    }


def test_get_transfer_history_from_postgresql():
    create_response = client.post(
        "/players",
        json={"name": "Bob"}
    )
    assert create_response.status_code == 201

    transfer_response = client.post(
        "/transfers",
        json={
            "sender": "Alice",
            "receiver": "Bob",
            "points": 30
        }
    )
    assert transfer_response.status_code == 201

    response = client.get("/transfers")

    assert response.status_code == 200

    history = response.json()["transfers"]

    assert len(history) == 1
    assert history[0]["transfer_id"] == 1
    assert history[0]["sender"] == "Alice"
    assert history[0]["receiver"] == "Bob"
    assert history[0]["points"] == 30
    assert history[0]["created_at"] is not None


def test_get_transfer_history_pagination_from_postgresql():
    create_response = client.post(
        "/players",
        json={"name": "Bob"}
    )
    assert create_response.status_code == 201

    transfers = [
        {
            "sender": "Alice",
            "receiver": "Bob",
            "points": 30
        },
        {
            "sender": "Bob",
            "receiver": "Alice",
            "points": 10
        },
        {
            "sender": "Alice",
            "receiver": "Bob",
            "points": 20
        },
    ]

    for transfer in transfers:
        response = client.post(
            "/transfers",
            json=transfer
        )
        assert response.status_code == 201

    response = client.get(
        "/transfers?limit=1&offset=1"
    )

    assert response.status_code == 200

    history = response.json()["transfers"]

    assert len(history) == 1
    assert history[0]["transfer_id"] == 2
    assert history[0]["sender"] == "Bob"
    assert history[0]["receiver"] == "Alice"
    assert history[0]["points"] == 10
    assert history[0]["created_at"] is not None
