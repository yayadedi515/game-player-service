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
