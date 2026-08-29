import pytest
from fastapi.testclient import TestClient

from main import app
from player_repository import transfer_score

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
            ["Alice", 90],
            ["Bob", 0],
            ["Charlie", 0]
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
    assert success is True

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
