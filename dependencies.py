from fastapi import Depends

from redis import Redis
from redis.backoff import NoBackoff
from redis.retry import Retry

from settings import get_settings
from player_repository import PlayerRepository
from player_service import PlayerService
from ranking_cache import RedisRankingCache



def get_player_repository():
    return PlayerRepository()


def get_redis_client(settings=Depends(get_settings)):
    return Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        decode_responses=True,
        socket_connect_timeout=(
            settings.redis_timeout_seconds
        ),
        socket_timeout=(
            settings.redis_timeout_seconds
        ),
        retry=Retry(
            NoBackoff(),
            0
        )
    )


def get_ranking_cache(
        redis_client=Depends(get_redis_client),
        settings=Depends(get_settings)
):
    return RedisRankingCache(
        redis_client,
        ttl_seconds=(
            settings.ranking_cache_ttl_seconds
        )
    )

def get_player_service(
        repository=Depends(get_player_repository),
        ranking_cache=Depends(get_ranking_cache)
):
    return PlayerService(
        repository,
        ranking_cache=ranking_cache
    )
