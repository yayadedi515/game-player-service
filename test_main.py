import pytest
from fastapi.testclient import TestClient

from main import app, service


client = TestClient(app)
@pytest.fixture(autouse=True)
def reset_service():
    service.players = {
        "Alice": 120,
        "Bob": 90
    }


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_existing_players():
    response = client.get("/players/Alice")

    assert response.status_code == 200
    assert response.json() == {"name": "Alice", "score": 120}


def test_get_players_missing_players():
    response = client.get("/players/Cindy")

    assert response.status_code == 404
    assert response.json() == {"detail": "Player not found"}


def test_get_ranking():
    response = client.get("/ranking")

    assert response.status_code == 200
    assert response.json() == {
        "ranking": [
            ["Alice", 120],
            ["Bob", 90]
        ]
    }


def test_create_player():
    response = client.post(
        "/players",
        json={"name": "Cindy"}
    )

    assert response.status_code == 201
    assert response.json() == {"name": "Cindy", "score": 0}

    new_response = client.get("/players/Cindy")
    assert new_response.status_code == 200
    assert new_response.json() == {"name": "Cindy", "score": 0}


def test_create_duplicate_player():
    response = client.post(
        "/players",
        json={"name": "Alice"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid or duplicate player"}


def test_create_player_without_name():
    response = client.post(
        "/players",
        json={}
    )
    assert response.status_code == 422


def test_create_player_empty_name():
    response = client.post(
        "/players",
        json={"name": "    "}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid or duplicate player"}


def test_delete_player_success():
    response = client.delete(
        "/players/Alice"
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Alice has been deleted"}
    new_response = client.get("/players/Alice")
    assert new_response.status_code == 404
    assert new_response.json() == {"detail": "Player not found"}

def test_delete_player_not_found():
    response = client.delete(
        "/players/Cindy"
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Player not found"}