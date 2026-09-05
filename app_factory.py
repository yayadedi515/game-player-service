from fastapi import FastAPI

from routers.health import router as health_router
from routers.players import router as players_router
from routers.transfers import router as transfers_router
from exception_handlers import register_exception_handlers
from routers.auth import router as auth_router


def create_app():
    app = FastAPI(title="Game Player Service")

    register_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(players_router)
    app.include_router(transfers_router)
    app.include_router(auth_router)

    return app
