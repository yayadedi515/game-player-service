from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
import logging

from exception_handlers import register_exception_handlers
from player_exceptions import (
    DuplicatePlayerError,
    InsufficientScoreError,
    InvalidTransferError,
    PlayerDeletionRestrictedError,
    PlayerNotFoundError,
    UnexpectedTransferResultError,
)


def test_player_not_found_error_returns_404():
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/test-error")
    def raise_error():
        raise PlayerNotFoundError

    client = TestClient(app)
    response = client.get("/test-error")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Player not found"
    }


@pytest.mark.parametrize(
    (
        "error_type",
        "expected_status",
        "expected_detail"
    ),
    [
        (
            DuplicatePlayerError,
            400,
            "Invalid or duplicate player"
        ),
        (
            PlayerDeletionRestrictedError,
            409,
            "Player has transfer history"
        ),
        (
            InsufficientScoreError,
            409,
            "Insufficient score"
        ),
        (
            InvalidTransferError,
            422,
            "Invalid transfer"
        ),
        (
            UnexpectedTransferResultError,
            500,
            "Unexpected transfer result"
        )
    ]
)
def test_business_error_returns_expected_response(
        error_type,
        expected_status,
        expected_detail
):
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/test-error")
    def raise_error():
        raise error_type

    client = TestClient(app)
    response = client.get("/test-error")

    assert response.status_code == expected_status
    assert response.json() == {
        "detail": expected_detail
    }


def test_unexpected_transfer_result_is_logged(caplog):
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/test-error")
    def raise_error():
        raise UnexpectedTransferResultError

    client = TestClient(app)

    with caplog.at_level(logging.ERROR):
        response = client.get("/test-error")

    assert response.status_code == 500
    assert "Unexpected business error" in caplog.text
    assert "UnexpectedTransferResultError" in caplog.text


def test_unhandled_exception_returns_safe_500_and_is_logged(
        caplog
):
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/test-error")
    def raise_error():
        raise RuntimeError(
            "Sensitive internal information"
        )

    client = TestClient(
        app,
        raise_server_exceptions=False
    )

    with caplog.at_level(logging.ERROR):
        response = client.get("/test-error")

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Internal server error"
    }
    assert "Unhandled server error" in caplog.text
    assert "RuntimeError" in caplog.text
    assert (
        "Sensitive internal information"
        not in response.text
    )