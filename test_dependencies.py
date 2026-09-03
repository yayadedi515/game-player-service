from dependencies import (
    get_player_repository,
    get_player_service,
    get_redis_client,
    get_ranking_cache,
)
from player_service import PlayerService
from player_repository import PlayerRepository
from player_repository_protocol import PlayerRepositoryProtocol
from ranking_cache import RedisRankingCache

class FakeSettings:
    redis_host = "cache"
    redis_port = 6380
    ranking_cache_ttl_seconds = 120


def test_get_player_repository_returns_player_repository():
    repository = get_player_repository()

    assert isinstance(repository, PlayerRepository)
    assert isinstance(repository, PlayerRepositoryProtocol)


def test_get_player_service_uses_provided_dependencies():
    repository = PlayerRepository()
    ranking_cache = object()

    service = get_player_service(
        repository,
        ranking_cache
    )

    assert isinstance(service, PlayerService)
    assert service.repository is repository
    assert service.ranking_cache is ranking_cache


def test_get_redis_client_uses_provided_settings():
    redis_client = get_redis_client(
        FakeSettings()
    )

    connection_settings = (
        redis_client
        .connection_pool
        .connection_kwargs
    )

    assert connection_settings["host"] == "cache"
    assert connection_settings["port"] == 6380
    assert (
        connection_settings["decode_responses"]
        is True
    )


def test_get_ranking_cache_uses_client_and_ttl():
    redis_client = object()

    cache = get_ranking_cache(
        redis_client,
        FakeSettings()
    )

    assert isinstance(cache, RedisRankingCache)
    assert cache.redis_client is redis_client
    assert cache.ttl_seconds == 120
