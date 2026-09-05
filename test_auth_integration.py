import pytest
from fastapi.testclient import TestClient

from database import get_connection
from main import app
from password_hasher import PasswordHasher


pytestmark = [
    pytest.mark.integration,
    pytest.mark.usefixtures("reset_test_database")
]


client = TestClient(app)


@pytest.mark.parametrize(
    (
        "username",
        "password"
    ),
    [
        (
            "aooshiro",
            "wrong-password"
        ),
        (
            "missing-user",
            "test-password-123!"
        )
    ]
)
def test_login_rejects_invalid_credentials(
        username,
        password
):
    register_response = client.post(
        "/auth/register",
        json={
            "username": "aooshiro",
            "password": "test-password-123!"
        }
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/token",
        data={
            "username": username,
            "password": password
        }
    )

    assert login_response.status_code == 401
    assert login_response.json() == {
        "detail": "Invalid username or password"
    }
    assert (
        login_response.headers[
            "www-authenticate"
        ]
        == "Bearer"
    )


def test_register_user_stores_password_hash_in_postgresql():
    plain_password = "test-password-123!"

    response = client.post(
        "/auth/register",
        json={
            "username": "aooshiro",
            "password": plain_password
        }
    )

    assert response.status_code == 201
    assert response.json() == {
        "username": "aooshiro"
    }

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT username, password_hash
                FROM users
                WHERE username = %s
                """,
                ("aooshiro",)
            )
            row = cursor.fetchone()

    assert row is not None

    username, password_hash = row

    assert username == "aooshiro"
    assert password_hash != plain_password
    assert PasswordHasher().verify_password(
        plain_password,
        password_hash
    )


def test_register_duplicate_username_returns_conflict():
    first_response = client.post(
        "/auth/register",
        json={
            "username": "aooshiro",
            "password": "first-test-password"
        }
    )
    second_response = client.post(
        "/auth/register",
        json={
            "username": "aooshiro",
            "password": "second-test-password"
        }
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "Username already exists"
    }

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM users
                WHERE username = %s
                """,
                ("aooshiro",)
            )
            row = cursor.fetchone()

    assert row[0] == 1


def test_registered_user_can_login_and_create_player():
    register_response = client.post(
        "/auth/register",
        json={
            "username": "aooshiro",
            "password": "test-password-123!"
        }
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/token",
        data={
            "username": "aooshiro",
            "password": "test-password-123!"
        }
    )

    assert login_response.status_code == 200

    token_data = login_response.json()

    assert token_data["token_type"] == "bearer"
    assert isinstance(
        token_data["access_token"],
        str
    )
    assert token_data["access_token"] != ""

    create_response = client.post(
        "/players",
        headers={
            "Authorization": (
                "Bearer "
                + token_data["access_token"]
            )
        },
        json={
            "name": "Diana"
        }
    )

    assert create_response.status_code == 201
    assert create_response.json() == {
        "name": "Diana",
        "score": 0
    }
