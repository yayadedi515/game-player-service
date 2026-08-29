import pytest
from fastapi.testclient import TestClient
from psycopg.errors import RestrictViolation

import main
from main import app
from transfer_result import TransferResult

client = TestClient(app)


class FakeRepository:
    def __init__(self):
        self.players = {
            "Alice": {
                "player_id": 1,
                "name": "Alice",
                "score": 120,
                "created_at": None
            },
            "Bob": {
                "player_id": 2,
                "name": "Bob",
                "score": 90,
                "created_at": None
            }
        }

        self.restricted_names = set()

    def get_ranking(self):
        return sorted(
            self.players.values(),
            key=lambda player: (
                -player["score"],
                player["name"]
            )
        )

    def delete_player(self, name):
        cleaned_name = name.strip()

        if cleaned_name == "":
            return None

        if cleaned_name in self.restricted_names:
            raise RestrictViolation(
                "Player is referenced by transfer history"
            )

        return self.players.pop(cleaned_name, None)

    def find_player_by_name(self, name):
        return self.players.get(name.strip())

    def create_player(self, name):
        cleaned_name = name.strip()

        if cleaned_name == "" or cleaned_name in self.players:
            return None

        next_player_id = max(
            player["player_id"]
            for player in self.players.values()
        ) + 1

        player = {
            "player_id": next_player_id,
            "name": cleaned_name,
            "score": 0,
            "created_at": None
        }

        self.players[cleaned_name] = player
        return player

    def add_score(self, name, points):
        cleaned_name = name.strip()
        player = self.players.get(cleaned_name)

        if player is None or points < 0:
            return None

        player["score"] += points
        return player

    def transfer_score(self, sender, receiver, points):
        cleaned_sender = sender.strip()
        cleaned_receiver = receiver.strip()

        if (
                not cleaned_sender
                or not cleaned_receiver
                or cleaned_sender == cleaned_receiver
                or points <= 0
        ):
            return TransferResult.INVALID_REQUEST

        sender_player = self.players.get(cleaned_sender)
        receiver_player = self.players.get(cleaned_receiver)

        if sender_player is None or receiver_player is None:
            return TransferResult.PLAYER_NOT_FOUND

        if sender_player["score"] < points:
            return TransferResult.INSUFFICIENT_SCORE

        sender_player["score"] -= points
        receiver_player["score"] += points
        return TransferResult.SUCCESS

@pytest.fixture(autouse=True)
def fake_repository():
    repository = FakeRepository()

    def provide_fake_repository():
        return repository

    app.dependency_overrides[
        main.get_player_repository
    ] = provide_fake_repository

    yield repository

    app.dependency_overrides.clear()


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


def test_get_ranking(fake_repository):
    fake_repository.players["Charlie"] = {
        "player_id": 3,
        "name": "Charlie",
        "score": 150,
        "created_at": None
    }

    response = client.get("/ranking")

    assert response.status_code == 200
    assert response.json() == {
        "ranking": [
            ["Charlie", 150],
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


def test_get_player_uses_repository_dependency(fake_repository):
    fake_repository.players["Diana"] = {
        "player_id": 7,
        "name": "Diana",
        "score": 345,
        "created_at": None
    }

    response = client.get("/players/Diana")

    assert response.status_code == 200
    assert response.json() == {
        "name": "Diana",
        "score": 345
    }


def test_delete_player_with_transfer_history_returns_conflict(
    fake_repository
):
    fake_repository.restricted_names.add("Alice")

    response = client.delete("/players/Alice")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Player has transfer history"
    }

    player = fake_repository.find_player_by_name("Alice")
    assert player is not None


def test_add_score_success(fake_repository):
    response = client.patch(
        "/players/Alice/score",
        json={"points": 30}
    )

    assert response.status_code == 200
    assert response.json() == {
        "name": "Alice",
        "score": 150
    }

    assert fake_repository.players["Alice"]["score"] == 150


def test_add_score_player_not_found():
    response = client.patch(
        "/players/Cindy/score",
        json={"points": 30}
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Player not found"
    }


def test_add_score_negative_points_returns_422(fake_repository):
    response = client.patch(
        "/players/Alice/score",
        json={"points": -1}
    )

    assert response.status_code == 422
    assert fake_repository.players["Alice"]["score"] == 120


def test_add_score_zero_points_is_allowed(fake_repository):
    response = client.patch(
        "/players/Alice/score",
        json={"points": 0}
    )

    assert response.status_code == 200
    assert response.json() == {
        "name": "Alice",
        "score": 120
    }
    assert fake_repository.players["Alice"]["score"] == 120


def test_transfer_score_success(fake_repository):
    response = client.post(
        "/transfers",
        json={
            "sender": "Alice",
            "receiver": "Bob",
            "points": 30
        }
    )

    assert response.status_code == 201
    assert response.json() == {
        "sender": "Alice",
        "receiver": "Bob",
        "points": 30
    }

    assert fake_repository.players["Alice"]["score"] == 90
    assert fake_repository.players["Bob"]["score"] == 120


def test_transfer_score_insufficient_score_returns_conflict(
        fake_repository
):
    response = client.post(
        "/transfers",
        json={
            "sender": "Alice",
            "receiver": "Bob",
            "points": 121
        }
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Insufficient score"
    }

    assert fake_repository.players["Alice"]["score"] == 120
    assert fake_repository.players["Bob"]["score"] == 90


def test_transfer_score_missing_player_returns_not_found(fake_repository):
    response = client.post(
        "/transfers",
        json={
            "sender": "Alice",
            "receiver": "Cindy",
            "points": 10
        }
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Player not found"
    }

    assert fake_repository.players["Alice"]["score"] == 120
    assert fake_repository.players["Bob"]["score"] == 90


def test_transfer_score_same_player_returns_422(fake_repository):
    response = client.post(
        "/transfers",
        json={
            "sender": "Alice",
            "receiver": "Alice",
            "points": 10
        }
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Invalid transfer"
    }

    assert fake_repository.players["Alice"]["score"] == 120


@pytest.mark.parametrize("points", [0, -1])
def test_transfer_score_non_positive_points_returns_422(
        fake_repository,
        points
):
    response = client.post(
        "/transfers",
        json={
            "sender": "Alice",
            "receiver": "Bob",
            "points": points
        }
    )

    assert response.status_code == 422
    assert fake_repository.players["Alice"]["score"] == 120
    assert fake_repository.players["Bob"]["score"] == 90
