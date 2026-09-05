from fastapi import FastAPI

from app_factory import create_app
from fastapi.testclient import TestClient
from player_exceptions import PlayerNotFoundError

def test_create_app_returns_a_fresh_configured_app():
    first_app = create_app()
    second_app = create_app()

    assert isinstance(first_app, FastAPI)
    assert first_app is not second_app

    paths = first_app.openapi()["paths"]

    assert "/health" in paths
    assert "/players/{name}" in paths
    assert "/ranking" in paths
    assert "/transfers" in paths


def test_create_app_registers_business_exception_handlers():
    app = create_app()

    @app.get("/test-error")
    def raise_error():
        raise PlayerNotFoundError

    client = TestClient(app)
    response = client.get("/test-error")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Player not found"
    }


def test_create_app_includes_auth_register_route():
    app = create_app()

    paths = app.openapi()["paths"]

    assert "/auth/register" in paths
