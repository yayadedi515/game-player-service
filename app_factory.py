from fastapi import FastAPI

from routers.health import router as health_router
from routers.players import router as players_router
from routers.transfers import router as transfers_router


def create_app():
    app = FastAPI(title="Game Player Service")

    app.include_router(health_router)
    app.include_router(players_router)
    app.include_router(transfers_router)

    return app
