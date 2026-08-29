from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from psycopg.errors import RestrictViolation

import player_repository


class PlayerCreate(BaseModel):
    name: str


app = FastAPI(title="Game Player Service")


def get_player_repository():
    return player_repository


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/players/{name}")
def get_player(
    name: str,
    repository=Depends(get_player_repository)
):
    player = repository.find_player_by_name(name)

    if player is None:
        raise HTTPException(
            status_code=404,
            detail="Player not found"
        )

    return {
        "name": player["name"],
        "score": player["score"]
    }


@app.get("/ranking")
def get_ranking(
    repository=Depends(get_player_repository)
):
    players = repository.get_ranking()

    ranking = [
        [player["name"], player["score"]]
        for player in players
    ]

    return {
        "ranking": ranking
    }


@app.post("/players", status_code=201)
def create_player(
    player: PlayerCreate,
    repository=Depends(get_player_repository)
):
    created_player = repository.create_player(player.name)

    if created_player is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid or duplicate player"
        )

    return {
        "name": created_player["name"],
        "score": created_player["score"]
    }


@app.delete("/players/{name}", status_code=200)
def delete_player(
    name: str,
    repository=Depends(get_player_repository)
):
    try:
        deleted_player = repository.delete_player(name)
    except RestrictViolation as error:
        raise HTTPException(
            status_code=409,
            detail="Player has transfer history"
        ) from error

    if deleted_player is None:
        raise HTTPException(
            status_code=404,
            detail="Player not found"
        )

    return {
        "message": (
            f"{deleted_player['name']} has been deleted"
        )
    }
