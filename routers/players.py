from fastapi import APIRouter, Depends

from dependencies import (
    get_current_user,
    get_player_service
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
    player = service.get_player(name)

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

    return {
        "ranking": service.get_ranking()
    }


@router.post(
    "/players",
    status_code=201,
    response_model=PlayerResponse
)
def create_player(
        player: PlayerCreate,
        service=Depends(get_player_service),
        _current_user=Depends(get_current_user)
):
    created_player = service.create_player(
        player.name
    )

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
    service=Depends(get_player_service),
    _current_user=Depends(get_current_user)
):
    deleted_player = service.delete_player(name)

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
    service=Depends(get_player_service),
    _current_user=Depends(get_current_user)
):
    player = service.add_score(
        name,
        score_add.points
    )

    return {
        "name": player["name"],
        "score": player["score"]
    }
