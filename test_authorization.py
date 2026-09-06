import pytest
from jwt import InvalidTokenError
from fastapi.testclient import TestClient

from app_factory import create_app

from dependencies import (
    get_current_user,
    get_player_service,
    get_token_service,
    get_user_repository
)


class FakePlayerService:
    def __init__(self):
        self.created_name = None
        self.score_request = None
        self.delete_request = None
        self.transfer_request = None

    def create_player(
            self,
            name,
            owner_user_id=None
    ):
        self.created_name = name
        return {
            "player_id": 1,
            "name": name,
            "score": 0,
            "created_at": None,
            "owner_user_id": owner_user_id
        }

    def add_score(
            self,
            name,
            points
    ):
        self.score_request = (
            name,
            points
        )

        return {
            "player_id": 1,
            "name": name,
            "score": 120 + points,
            "created_at": None,
            "owner_user_id": 1
        }

    def delete_player(
            self,
            name,
            current_user
    ):
        self.delete_request = (
            name,
            current_user
        )

        return {
            "player_id": 1,
            "name": name,
            "score": 120,
            "created_at": None,
            "owner_user_id": current_user["user_id"]
        }

    def transfer_score(
            self,
            sender,
            receiver,
            points,
            current_user
    ):
        self.transfer_request = (
            sender,
            receiver,
            points,
            current_user
        )

        return {
            "sender": sender,
            "receiver": receiver,
            "points": points
        }


@pytest.mark.parametrize(
    (
        "method",
        "path",
        "request_body"
    ),
    [
        (
            "POST",
            "/players",
            {"name": "Diana"}
        ),
        (
            "DELETE",
            "/players/Alice",
            None
        ),
        (
            "PATCH",
            "/players/Alice/score",
            {"points": 30}
        ),
        (
            "POST",
            "/transfers",
            {
                "sender": "Alice",
                "receiver": "Bob",
                "points": 30
            }
        )
    ]
)
def test_write_endpoints_require_access_token(
        method,
        path,
        request_body
):
    app = create_app()

    app.dependency_overrides[
        get_player_service
    ] = lambda: FakePlayerService()

    client = TestClient(app)

    response = client.request(
        method,
        path,
        json=request_body
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Not authenticated"
    }
    assert (
        response.headers["www-authenticate"]
        == "Bearer"
    )


def test_authenticated_user_can_create_player():
    app = create_app()
    service = FakePlayerService()

    app.dependency_overrides[
        get_player_service
    ] = lambda: service
    app.dependency_overrides[
        get_current_user
    ] = lambda: {
        "user_id": 1,
        "username": "aooshiro",
        "created_at": None,
        "role": "user"
    }

    client = TestClient(app)

    response = client.post(
        "/players",
        json={
            "name": "Diana"
        }
    )

    assert response.status_code == 201
    assert response.json() == {
        "name": "Diana",
        "score": 0
    }
    assert service.created_name == "Diana"


def test_write_endpoint_rejects_invalid_access_token():
    class InvalidTokenService:
        def decode_access_token(self, token):
            raise InvalidTokenError(
                "Invalid token"
            )

    class UnusedUserRepository:
        def find_user_by_username(self, username):
            raise AssertionError(
                "Invalid token must not query user"
            )

    app = create_app()

    app.dependency_overrides[
        get_player_service
    ] = lambda: FakePlayerService()
    app.dependency_overrides[
        get_token_service
    ] = lambda: InvalidTokenService()
    app.dependency_overrides[
        get_user_repository
    ] = lambda: UnusedUserRepository()

    client = TestClient(app)

    response = client.post(
        "/players",
        headers={
            "Authorization": "Bearer invalid-token"
        },
        json={
            "name": "Diana"
        }
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Could not validate credentials"
    }
    assert (
        response.headers["www-authenticate"]
        == "Bearer"
    )


def test_regular_user_cannot_add_score():
    app = create_app()
    service = FakePlayerService()

    app.dependency_overrides[
        get_player_service
    ] = lambda: service

    app.dependency_overrides[
        get_current_user
    ] = lambda: {
        "user_id": 1,
        "username": "regular-user",
        "created_at": None,
        "role": "user"
    }

    client = TestClient(app)

    response = client.patch(
        "/players/Alice/score",
        json={
            "points": 30
        }
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Permission denied"
    }
    assert service.score_request is None


def test_admin_user_can_add_score():
    app = create_app()
    service = FakePlayerService()

    app.dependency_overrides[
        get_player_service
    ] = lambda: service

    app.dependency_overrides[
        get_current_user
    ] = lambda: {
        "user_id": 2,
        "username": "admin-user",
        "created_at": None,
        "role": "admin"
    }

    client = TestClient(app)

    response = client.patch(
        "/players/Alice/score",
        json={
            "points": 30
        }
    )

    assert response.status_code == 200
    assert response.json() == {
        "name": "Alice",
        "score": 150
    }
    assert service.score_request == (
        "Alice",
        30
    )


def test_delete_player_passes_current_user_to_service():
    app = create_app()
    service = FakePlayerService()

    current_user = {
        "user_id": 1,
        "username": "player-owner",
        "created_at": None,
        "role": "user"
    }

    app.dependency_overrides[
        get_player_service
    ] = lambda: service

    app.dependency_overrides[
        get_current_user
    ] = lambda: current_user

    client = TestClient(app)

    response = client.delete(
        "/players/Alice"
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Alice has been deleted"
    }
    assert service.delete_request == (
        "Alice",
        current_user
    )


def test_transfer_passes_current_user_to_service():
    app = create_app()
    service = FakePlayerService()

    current_user = {
        "user_id": 1,
        "username": "player-owner",
        "created_at": None,
        "role": "user"
    }

    app.dependency_overrides[
        get_player_service
    ] = lambda: service

    app.dependency_overrides[
        get_current_user
    ] = lambda: current_user

    client = TestClient(app)

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
    assert service.transfer_request == (
        "Alice",
        "Bob",
        30,
        current_user
    )
