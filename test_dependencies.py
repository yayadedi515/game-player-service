from dependencies import (
    get_player_repository,
    get_player_service
)
from player_service import PlayerService
from player_repository import PlayerRepository
from player_repository_protocol import PlayerRepositoryProtocol


def test_get_player_repository_returns_player_repository():
    repository = get_player_repository()

    assert isinstance(repository, PlayerRepository)
    assert isinstance(repository, PlayerRepositoryProtocol)


def test_get_player_service_uses_provided_repository():
    repository = PlayerRepository()

    service = get_player_service(repository)

    assert isinstance(service, PlayerService)
    assert service.repository is repository
