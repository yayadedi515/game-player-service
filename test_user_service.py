import pytest

from user_exceptions import DuplicateUserError
from user_service import UserService


class FakeUserRepository:
    def __init__(self):
        self.create_request = None
        self.create_succeeds = True

    def create_user(
            self,
            username,
            password_hash
    ):
        self.create_request = (
            username,
            password_hash
        )
        if not self.create_succeeds:
            return None

        return {
            "user_id": 1,
            "username": username,
            "password_hash": password_hash,
            "created_at": None
        }


class FakePasswordHasher:
    def __init__(self):
        self.plain_password = None

    def hash_password(self, plain_password):
        self.plain_password = plain_password
        return "generated-password-hash"


def test_register_user_hashes_password_before_repository():
    repository = FakeUserRepository()
    password_hasher = FakePasswordHasher()
    service = UserService(
        repository,
        password_hasher
    )

    user = service.register_user(
        "aooshiro",
        "test-password-123!"
    )

    assert (
        password_hasher.plain_password
        == "test-password-123!"
    )
    assert repository.create_request == (
        "aooshiro",
        "generated-password-hash"
    )
    assert user["username"] == "aooshiro"
    assert "password_hash" not in user


def test_register_duplicate_user_raises_duplicate_user_error():
    repository = FakeUserRepository()
    repository.create_succeeds = False
    service = UserService(
        repository,
        FakePasswordHasher()
    )

    with pytest.raises(DuplicateUserError):
        service.register_user(
            "aooshiro",
            "test-password-123!"
        )
