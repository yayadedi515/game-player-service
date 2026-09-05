from token_service import TokenService
from token_service_protocol import TokenServiceProtocol

import pytest
from jwt import InvalidTokenError


def test_access_token_can_restore_subject():
    service = TokenService(
        secret_key=(
            "test-only-jwt-secret-key-123456789"
        ),
        expire_minutes=30
    )

    token = service.create_access_token(
        "aooshiro"
    )
    subject = service.decode_access_token(
        token
    )

    assert isinstance(token, str)
    assert token != "aooshiro"
    assert subject == "aooshiro"


def test_access_token_rejects_wrong_secret():
    issuer = TokenService(
        secret_key=(
            "first-test-jwt-secret-key-123456789"
        ),
        expire_minutes=30
    )
    verifier = TokenService(
        secret_key=(
            "second-test-jwt-secret-key-12345678"
        ),
        expire_minutes=30
    )

    token = issuer.create_access_token(
        "aooshiro"
    )

    with pytest.raises(InvalidTokenError):
        verifier.decode_access_token(token)


def test_access_token_rejects_expired_token():
    service = TokenService(
        secret_key=(
            "test-only-jwt-secret-key-123456789"
        ),
        expire_minutes=-1
    )

    token = service.create_access_token(
        "aooshiro"
    )

    with pytest.raises(InvalidTokenError):
        service.decode_access_token(token)


def test_token_service_satisfies_protocol():
    service = TokenService(
        secret_key="test-secret-key-at-least-32-characters",
        expire_minutes=30
    )

    assert isinstance(
        service,
        TokenServiceProtocol
    )
