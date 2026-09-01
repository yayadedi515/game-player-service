from fastapi import Depends

from player_repository import PlayerRepository
from player_service import PlayerService


def get_player_repository():
    return PlayerRepository()


def get_player_service(
        repository=Depends(get_player_repository)
):
    return PlayerService(repository)
