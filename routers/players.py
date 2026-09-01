from fastapi import APIRouter, Depends, HTTPException

from dependencies import get_player_service
from player_exceptions import (
    PlayerNotFoundError,
    DuplicatePlayerError,
    PlayerDeletionRestrictedError,
)
from schemas import (
    PlayerName,
    PlayerResponse,
    RankingResponse,
    PlayerCreate,
    PlayerDeleteResponse,
    ScoreAdd,
)

router = APIRouter(tags=["Players"])


@router.get(
    "/players/{name}",
    response_model=PlayerResponse
)
def get_player(
        name: PlayerName,
        service=Depends(get_player_service)
):
    try:
        player = service.get_player(name)
    except PlayerNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail="Player not found"
        ) from error

    return {
        "name": player["name"],
        "score": player["score"]
    }


@router.get(
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


@router.post(
    "/players",
    status_code=201,
    response_model=PlayerResponse
)
def create_player(
    player: PlayerCreate,
    service=Depends(get_player_service)
):
    try:
        created_player = service.create_player(player.name)
    except DuplicatePlayerError as error:
        raise HTTPException(
            status_code=400,
            detail="Invalid or duplicate player"
        ) from error

    return {
        "name": created_player["name"],
        "score": created_player["score"]
    }


@router.delete(
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

    except PlayerNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail="Player not found"
        ) from error

    except PlayerDeletionRestrictedError as error:
        raise HTTPException(
            status_code=409,
            detail="Player has transfer history"
        ) from error

    return {
        "message": (
            f"{deleted_player['name']} has been deleted"
        )
    }


@router.patch(
    "/players/{name}/score",
    response_model=PlayerResponse
)
def add_player_score(
        name: PlayerName,
        score_add: ScoreAdd,
        service=Depends(get_player_service)
):
    try:
        player = service.add_score(
            name,
            score_add.points
        )
    except PlayerNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail="Player not found"
        ) from error

    return {
        "name": player["name"],
        "score": player["score"]
    }
