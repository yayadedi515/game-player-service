import pytest
from fastapi.testclient import TestClient

import main
import dependencies
from main import app
from player_repository import PlayerRepository
from player_repository_protocol import PlayerRepositoryProtocol
from player_exceptions import (
    InsufficientScoreError,
    InvalidTransferError,
    PlayerDeletionRestrictedError,
    DuplicatePlayerError,
    PlayerNotFoundError,
    UnexpectedTransferResultError,
)

client = TestClient(app)


class FakeService:
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
        self.unexpected_transfer_result = False

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
            raise PlayerNotFoundError

        if cleaned_name in self.restricted_names:
            raise PlayerDeletionRestrictedError

        player = self.players.pop(cleaned_name, None)

        if player is None:
            raise PlayerNotFoundError

        return player

    def get_player(self, name):
        cleaned_name = name.strip()
        player = self.players.get(cleaned_name)

        if player is None:
            raise PlayerNotFoundError

        return player

    def create_player(self, name):
        cleaned_name = name.strip()

        if cleaned_name == "" or cleaned_name in self.players:
            raise DuplicatePlayerError

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
            raise PlayerNotFoundError

        player["score"] += points
        return player

    def transfer_score(self, sender, receiver, points):
        self.transfer_score_call_count += 1
        if self.unexpected_transfer_result:
            raise UnexpectedTransferResultError

        cleaned_sender = sender.strip()
        cleaned_receiver = receiver.strip()

        if (
                not cleaned_sender
                or not cleaned_receiver
                or cleaned_sender == cleaned_receiver
                or points <= 0
        ):
            raise InvalidTransferError

        sender_player = self.players.get(cleaned_sender)
        receiver_player = self.players.get(cleaned_receiver)

        if sender_player is None or receiver_player is None:
            raise PlayerNotFoundError

        if sender_player["score"] < points:
            raise InsufficientScoreError

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

        return {
            "sender": cleaned_sender,
            "receiver": cleaned_receiver,
            "points": points
        }

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
def fake_service():
    service = FakeService()

    def provide_fake_service():
        return service

    app.dependency_overrides[
        dependencies.get_player_service
    ] = provide_fake_service

    try:
        yield service
    finally:
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


def test_get_ranking(fake_service):
    fake_service.players["Charlie"] = {
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


def test_get_player_uses_service_dependency(
        fake_service
):
    fake_service.players["Diana"] = {
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
    fake_service
):
    fake_service.restricted_names.add("Alice")

    response = client.delete("/players/Alice")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Player has transfer history"
    }

    player = fake_service.get_player("Alice")
    assert player is not None


def test_add_score_success(fake_service):
    response = client.patch(
        "/players/Alice/score",
        json={"points": 30}
    )

    assert response.status_code == 200
    assert response.json() == {
        "name": "Alice",
        "score": 150
    }

    assert fake_service.players["Alice"]["score"] == 150


def test_add_score_player_not_found():
    response = client.patch(
        "/players/Cindy/score",
        json={"points": 30}
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Player not found"
    }


def test_add_score_negative_points_returns_422(fake_service):
    response = client.patch(
        "/players/Alice/score",
        json={"points": -1}
    )

    assert response.status_code == 422
    assert fake_service.players["Alice"]["score"] == 120


def test_add_score_zero_points_is_allowed(fake_service):
    response = client.patch(
        "/players/Alice/score",
        json={"points": 0}
    )

    assert response.status_code == 200
    assert response.json() == {
        "name": "Alice",
        "score": 120
    }
    assert fake_service.players["Alice"]["score"] == 120


def test_transfer_score_success(fake_service):
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

    assert fake_service.players["Alice"]["score"] == 90
    assert fake_service.players["Bob"]["score"] == 120


def test_transfer_score_insufficient_score_returns_conflict(
        fake_service
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

    assert fake_service.players["Alice"]["score"] == 120
    assert fake_service.players["Bob"]["score"] == 90


def test_transfer_score_missing_player_returns_not_found(fake_service):
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

    assert fake_service.players["Alice"]["score"] == 120
    assert fake_service.players["Bob"]["score"] == 90


def test_transfer_score_same_player_returns_422(fake_service):
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
    assert fake_service.players["Alice"]["score"] == 120


@pytest.mark.parametrize("points", [0, -1])
def test_transfer_score_non_positive_points_returns_422(
        fake_service,
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
    assert fake_service.players["Alice"]["score"] == 120
    assert fake_service.players["Bob"]["score"] == 90


def test_get_transfer_history_returns_transfers(fake_service):
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
        fake_service
):
    name = "A" * 51

    response = client.post(
        "/players",
        json={"name": name}
    )

    assert response.status_code == 422
    assert name not in fake_service.players


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
        fake_service
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
    assert fake_service.transfer_history == []


def test_transfer_same_player_is_rejected_before_repository(
        fake_service
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
    assert fake_service.transfer_score_call_count == 0


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
        fake_service
):
    response = client.get(
        f"/transfers?{query}"
    )

    assert response.status_code == 422
    assert (
        fake_service
        .get_transfer_history_call_count
        == 0
    )


def test_transfer_score_unexpected_error_returns_500(fake_service):
    fake_service.unexpected_transfer_result = True

    response = client.post(
        "/transfers",
        json={
            "sender": "Alice",
            "receiver": "Bob",
            "points": 30
        }
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Unexpected transfer result"
    }


def test_openapi_groups_routes_by_domain():
    schema = app.openapi()

    assert schema["paths"]["/health"]["get"]["tags"] == [
        "Health"
    ]
    assert schema["paths"]["/players/{name}"]["get"]["tags"] == [
        "Players"
    ]
    assert schema["paths"]["/transfers"]["post"]["tags"] == [
        "Transfers"
    ]
