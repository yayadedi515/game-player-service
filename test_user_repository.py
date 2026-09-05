import pytest

from user_repository import UserRepository


pytestmark = [
    pytest.mark.integration,
    pytest.mark.usefixtures("reset_test_database")
]


def test_create_user_stores_password_hash():
    repository = UserRepository()

    user = repository.create_user(
        "aooshiro",
        "stored-password-hash"
    )

    assert user["user_id"] == 1
    assert user["username"] == "aooshiro"
    assert user["password_hash"] == "stored-password-hash"
    assert user["created_at"] is not None


def test_find_user_by_username_returns_user():
    repository = UserRepository()
    created_user = repository.create_user(
        "aooshiro",
        "stored-password-hash"
    )

    found_user = repository.find_user_by_username(
        "aooshiro"
    )

    assert found_user == created_user


def test_create_duplicate_user_returns_none():
    repository = UserRepository()
    repository.create_user(
        "aooshiro",
        "first-password-hash"
    )

    duplicate_user = repository.create_user(
        "aooshiro",
        "second-password-hash"
    )

    assert duplicate_user is None


def test_find_missing_user_returns_none():
    repository = UserRepository()

    user = repository.find_user_by_username(
        "missing-user"
    )

    assert user is None


def test_user_repository_strips_username_whitespace():
    repository = UserRepository()

    created_user = repository.create_user(
        "  aooshiro  ",
        "stored-password-hash"
    )
    found_user = repository.find_user_by_username(
        "  aooshiro  "
    )

    assert created_user["username"] == "aooshiro"
    assert found_user == created_user
