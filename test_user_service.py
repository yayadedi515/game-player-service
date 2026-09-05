import pytest

from user_exceptions import (
    DuplicateUserError,
    InvalidCredentialsError
)
from user_service import UserService


class FakeUserRepository:
    def __init__(self):
        self.create_request = None
        self.create_succeeds = True
        self.requested_username = None
        self.find_result = {
            "user_id": 1,
            "username": "aooshiro",
            "password_hash": "stored-password-hash",
            "created_at": None
        }

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

    def find_user_by_username(self, username):
        self.requested_username = username
        return self.find_result


class FakePasswordHasher:
    def __init__(self):
        self.plain_password = None
        self.verify_request = None
        self.password_matches = True

    def hash_password(self, plain_password):
        self.plain_password = plain_password
        return "generated-password-hash"

    def verify_password(
            self,
            plain_password,
            password_hash
    ):
        self.verify_request = (
            plain_password,
            password_hash
        )
        return self.password_matches


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


def test_authenticate_user_verifies_stored_password_hash():
    repository = FakeUserRepository()
    password_hasher = FakePasswordHasher()
    service = UserService(
        repository,
        password_hasher
    )

    user = service.authenticate_user(
        "aooshiro",
        "test-password-123!"
    )

    assert (
        repository.requested_username
        == "aooshiro"
    )
    assert password_hasher.verify_request == (
        "test-password-123!",
        "stored-password-hash"
    )
    assert user == {
        "user_id": 1,
        "username": "aooshiro",
        "created_at": None
    }


def test_authenticate_missing_user_raises_invalid_credentials():
    repository = FakeUserRepository()
    repository.find_result = None
    password_hasher = FakePasswordHasher()
    service = UserService(
        repository,
        password_hasher
    )

    with pytest.raises(InvalidCredentialsError):
        service.authenticate_user(
            "missing-user",
            "test-password-123!"
        )

    assert password_hasher.verify_request is None


def test_authenticate_wrong_password_raises_invalid_credentials():
    repository = FakeUserRepository()
    password_hasher = FakePasswordHasher()
    password_hasher.password_matches = False
    service = UserService(
        repository,
        password_hasher
    )

    with pytest.raises(InvalidCredentialsError):
        service.authenticate_user(
            "aooshiro",
            "wrong-test-password"
        )
