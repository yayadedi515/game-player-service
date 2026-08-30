from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from psycopg.errors import RestrictViolation

import player_repository
from schemas import (
    HealthResponse,
    PlayerCreate,
    PlayerDeleteResponse,
    PlayerName,
    PlayerResponse,
    RankingResponse,
    ScoreAdd,
    ScoreTransfer,
    TransferHistoryResponse,
    TransferResponse,
)
from transfer_result import TransferResult
from player_service import PlayerService


app = FastAPI(title="Game Player Service")


def get_player_repository():
    return player_repository


def get_player_service(
        repository=Depends(get_player_repository)
):
    return PlayerService(repository)


@app.get(
    "/health",
    response_model=HealthResponse
)
def health_check():
    return {"status": "ok"}


@app.get(
    "/players/{name}",
    response_model=PlayerResponse
)
def get_player(
    name: PlayerName,
    service=Depends(get_player_service)
):
    player = service.get_player(name)

    if player is None:
        raise HTTPException(
            status_code=404,
            detail="Player not found"
        )

    return {
        "name": player["name"],
        "score": player["score"]
    }


@app.get(
    "/ranking",
    response_model=RankingResponse
)
def get_ranking(
    service=Depends(get_player_service)
):
    players = service.get_ranking()

    ranking = [
        {
            "name": player["name"],
            "score": player["score"]
        }
        for player in players
    ]

    return {
        "ranking": ranking
    }


@app.post(
    "/players",
    status_code=201,
    response_model=PlayerResponse
)
def create_player(
    player: PlayerCreate,
    service=Depends(get_player_service)
):
    created_player = service.create_player(
        player.name
    )

    if created_player is None:
        raise HTTPException(
            status_code=400,
            detail="Invalid or duplicate player"
        )

    return {
        "name": created_player["name"],
        "score": created_player["score"]
    }


@app.delete(
    "/players/{name}",
    status_code=200,
    response_model=PlayerDeleteResponse
)
def delete_player(
    name: PlayerName,
    service=Depends(get_player_service)
):
    try:
        deleted_player = service.delete_player(name)
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


@app.patch(
    "/players/{name}/score",
    response_model=PlayerResponse
)
def add_player_score(
        name: PlayerName,
        score_add: ScoreAdd,
        service=Depends(get_player_service)
):
    player = service.add_score(
        name,
        score_add.points
    )

    if player is None:
        raise HTTPException(
            status_code=404,
            detail="Player not found"
        )

    return {
        "name": player["name"],
        "score": player["score"]
    }


@app.post(
    "/transfers",
    status_code=201,
    response_model=TransferResponse
)
def transfer_player_score(
        transfer: ScoreTransfer,
        service=Depends(get_player_service)
):
    result = service.transfer_score(
        transfer.sender,
        transfer.receiver,
        transfer.points
    )

    if result is TransferResult.PLAYER_NOT_FOUND:
        raise HTTPException(
            status_code=404,
            detail="Player not found"
        )

    if result is TransferResult.INSUFFICIENT_SCORE:
        raise HTTPException(
            status_code=409,
            detail="Insufficient score"
        )

    if result is TransferResult.INVALID_REQUEST:
        raise HTTPException(
            status_code=422,
            detail="Invalid transfer"
        )

    if result is not TransferResult.SUCCESS:
        raise HTTPException(
            status_code=500,
            detail="Unexpected transfer result"
        )

    return {
        "sender": transfer.sender.strip(),
        "receiver": transfer.receiver.strip(),
        "points": transfer.points
    }


@app.get(
    "/transfers",
    response_model=TransferHistoryResponse
)
def get_transfer_history(
        limit: Annotated[
            int,
            Query(ge=1, le=100)
        ] = 20,
        offset: Annotated[
            int,
            Query(ge=0)
        ] = 0,
        service=Depends(get_player_service)
):
    return {
        "transfers": service.get_transfer_history(
            limit=limit,
            offset=offset
        )
    }
