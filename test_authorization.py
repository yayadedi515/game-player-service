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

    def create_player(self, name):
        self.created_name = name
        return {
            "name": name,
            "score": 0
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
        "created_at": None
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
