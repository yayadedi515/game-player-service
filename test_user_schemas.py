import pytest
from pydantic import ValidationError, SecretStr

from schemas import UserRegister, TokenResponse


def test_user_register_validates_and_cleans_input():
    request = UserRegister(
        username="  aooshiro  ",
        password="test-password-123!"
    )

    assert request.username == "aooshiro"
    assert isinstance(request.password, SecretStr)
    assert (
        request.password.get_secret_value()
        == "test-password-123!"
    )


def test_user_register_rejects_short_password():
    with pytest.raises(ValidationError):
        UserRegister(
            username="aooshiro",
            password="short"
        )


def test_user_register_rejects_blank_username():
    with pytest.raises(ValidationError):
        UserRegister(
            username="       ",
            password="test-password-123!"
        )


def test_token_response_contains_bearer_token():
    response = TokenResponse(
        access_token="example-token",
        token_type="bearer"
    )

    assert response.access_token == "example-token"
    assert response.token_type == "bearer"
