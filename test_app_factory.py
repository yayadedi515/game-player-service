from fastapi import FastAPI

from app_factory import create_app


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