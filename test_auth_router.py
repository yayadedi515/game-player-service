from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from dependencies import get_user_service
from routers.auth import router as auth_router
from exception_handlers import register_exception_handlers
from user_exceptions import DuplicateUserError


class FakeUserService:
    def __init__(self):
        self.register_request = None
        self.reject_registration = False

    def register_user(
            self,
            username,
            plain_password
    ):
        if self.reject_registration:
            raise DuplicateUserError

        self.register_request = (
            username,
            plain_password
        )

        return {
            "user_id": 1,
            "username": username,
            "created_at": None
        }


fake_service = FakeUserService()
app = FastAPI()
register_exception_handlers(app)
app.include_router(auth_router)
app.dependency_overrides[
    get_user_service
] = lambda: fake_service
client = TestClient(app)


def test_register_user_uses_user_service():
    response = client.post(
        "/auth/register",
        json={
            "username": "aooshiro",
            "password": "test-password-123!"
        }
    )

    assert response.status_code == 201
    assert response.json() == {
        "username": "aooshiro"
    }
    assert fake_service.register_request == (
        "aooshiro",
        "test-password-123!"
    )


def test_register_duplicate_user_returns_conflict():
    fake_service.reject_registration = True

    try:
        response = client.post(
            "/auth/register",
            json={
                "username": "aooshiro",
                "password": "test-password-123!"
            }
        )
    finally:
        fake_service.reject_registration = False

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Username already exists"
    }


@pytest.mark.parametrize(
    "payload",
    [
        {
            "username": "aooshiro",
            "password": "short"
        },
        {
            "username": "     ",
            "password": "test-password-123!"
        }
    ]
)
def test_register_user_rejects_invalid_input(payload):
    fake_service.register_request = None

    response = client.post(
        "/auth/register",
        json=payload
    )

    assert response.status_code == 422
    assert fake_service.register_request is None
