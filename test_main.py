import pytest
from fastapi.testclient import TestClient
from psycopg.errors import RestrictViolation

import main
from main import app
from transfer_result import TransferResult

client = TestClient(app)


class FakeRepository:
    def __init__(self):
        self.transfer_score_call_count = 0
        self.get_transfer_history_call_count = 0
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
        self.transfer_history = []

    def get_ranking(self):
        return sorted(
            [
                player.copy()
                for player in self.players.values()
            ],
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
        self.transfer_score_call_count += 1
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
        transfer_id = len(self.transfer_history) + 1

        self.transfer_history.insert(0, {
            "transfer_id": transfer_id,
            "sender": cleaned_sender,
            "receiver": cleaned_receiver,
            "points": points,
            "created_at": None
        })

        return TransferResult.SUCCESS

    def get_transfer_history(
            self,
            limit=20,
            offset=0
    ):
        self.get_transfer_history_call_count += 1
        selected_transfers = self.transfer_history[
                             offset:offset + limit
                             ]

        return [
            transfer.copy()
            for transfer in selected_transfers
        ]

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
            {
                "name": "Charlie",
                "score": 150
            },
            {
                "name": "Alice",
                "score": 120
            },
            {
                "name": "Bob",
                "score": 90
            }
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
    detail = response.json()["detail"]

    assert detail[0]["loc"] == ["body", "name"]
    assert detail[0]["type"] == "string_too_short"


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
    detail = response.json()["detail"]

    assert detail[0]["loc"] == ["body"]
    assert detail[0]["type"] == "value_error"
    assert (
            "Sender and receiver must be different"
            in detail[0]["msg"]
    )
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


def test_get_transfer_history_returns_transfers(fake_repository):
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
    assert response.json() == {
        "transfers": [
            {
                "transfer_id": 1,
                "sender": "Alice",
                "receiver": "Bob",
                "points": 30,
                "created_at": None
            }
        ]
    }


def test_get_transfer_history_empty_returns_empty_list():
    response = client.get("/transfers")

    assert response.status_code == 200
    assert response.json() == {
        "transfers": []
    }


def test_create_player_name_with_50_characters_is_allowed():
    name = "A" * 50

    response = client.post(
        "/players",
        json={"name": name}
    )

    assert response.status_code == 201
    assert response.json() == {
        "name": name,
        "score": 0
    }


def test_create_player_name_longer_than_50_returns_422(
        fake_repository
):
    name = "A" * 51

    response = client.post(
        "/players",
        json={"name": name}
    )

    assert response.status_code == 422
    assert name not in fake_repository.players


def test_get_player_blank_name_returns_422():
    response = client.get("/players/%20%20%20")

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("DELETE", "/players/%20%20%20", None),
        (
            "PATCH",
            "/players/%20%20%20/score",
            {"points": 10}
        ),
    ],
)
def test_player_path_blank_name_returns_422(
        method,
        path,
        body
):
    response = client.request(
        method,
        path,
        json=body
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("sender", "receiver"),
    [
        ("A" * 51, "Bob"),
        ("Alice", "B" * 51),
    ],
)
def test_transfer_player_name_longer_than_50_returns_422(
        sender,
        receiver,
        fake_repository
):
    response = client.post(
        "/transfers",
        json={
            "sender": sender,
            "receiver": receiver,
            "points": 10
        }
    )

    assert response.status_code == 422
    assert fake_repository.transfer_history == []


def test_transfer_same_player_is_rejected_before_repository(
        fake_repository
):
    response = client.post(
        "/transfers",
        json={
            "sender": "  Alice  ",
            "receiver": "Alice",
            "points": 10
        }
    )

    assert response.status_code == 422
    assert fake_repository.transfer_score_call_count == 0


def test_get_player_openapi_uses_player_response():
    openapi_schema = app.openapi()

    response_schema = (
        openapi_schema["paths"]["/players/{name}"]
        ["get"]["responses"]["200"]
        ["content"]["application/json"]["schema"]
    )

    assert response_schema == {
        "$ref": "#/components/schemas/PlayerResponse"
    }


@pytest.mark.parametrize(
    ("path", "method", "status_code"),
    [
        ("/players", "post", "201"),
        ("/players/{name}/score", "patch", "200"),
    ],
)
def test_player_write_openapi_uses_player_response(
        path,
        method,
        status_code
):
    openapi_schema = app.openapi()

    response_schema = (
        openapi_schema["paths"][path]
        [method]["responses"][status_code]
        ["content"]["application/json"]["schema"]
    )

    assert response_schema == {
        "$ref": "#/components/schemas/PlayerResponse"
    }


@pytest.mark.parametrize(
    (
        "method",
        "status_code",
        "response_model_name"
    ),
    [
        ("post", "201", "TransferResponse"),
        ("get", "200", "TransferHistoryResponse"),
    ],
)
def test_transfer_openapi_uses_response_models(
        method,
        status_code,
        response_model_name
):
    openapi_schema = app.openapi()

    response_schema = (
        openapi_schema["paths"]["/transfers"]
        [method]["responses"][status_code]
        ["content"]["application/json"]["schema"]
    )

    assert response_schema == {
        "$ref": (
            "#/components/schemas/"
            f"{response_model_name}"
        )
    }


def test_ranking_openapi_uses_ranking_response():
    openapi_schema = app.openapi()

    response_schema = (
        openapi_schema["paths"]["/ranking"]
        ["get"]["responses"]["200"]
        ["content"]["application/json"]["schema"]
    )

    assert response_schema == {
        "$ref": "#/components/schemas/RankingResponse"
    }


@pytest.mark.parametrize(
    (
        "path",
        "method",
        "response_model_name"
    ),
    [
        ("/health", "get", "HealthResponse"),
        (
            "/players/{name}",
            "delete",
            "PlayerDeleteResponse"
        ),
    ],
)
def test_simple_openapi_uses_response_models(
        path,
        method,
        response_model_name
):
    openapi_schema = app.openapi()

    response_schema = (
        openapi_schema["paths"][path]
        [method]["responses"]["200"]
        ["content"]["application/json"]["schema"]
    )

    assert response_schema == {
        "$ref": (
            "#/components/schemas/"
            f"{response_model_name}"
        )
    }


def test_get_transfer_history_supports_pagination():
    transfers = [
        {
            "sender": "Alice",
            "receiver": "Bob",
            "points": 10
        },
        {
            "sender": "Bob",
            "receiver": "Alice",
            "points": 5
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


@pytest.mark.parametrize(
    "query",
    [
        "limit=0",
        "limit=101",
        "offset=-1",
    ],
)
def test_get_transfer_history_rejects_invalid_pagination(
        query,
        fake_repository
):
    response = client.get(
        f"/transfers?{query}"
    )

    assert response.status_code == 422
    assert (
        fake_repository
        .get_transfer_history_call_count
        == 0
    )
