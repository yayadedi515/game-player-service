import json

from ranking_cache import RedisRankingCache
from redis.exceptions import (
    ConnectionError as RedisConnectionError
)


class FakeRedis:
    def __init__(self, cached_value=None):
        self.cached_value = cached_value
        self.requested_key = None
        self.set_request = None
        self.deleted_key = None

    def get(self, key):
        self.requested_key = key
        return self.cached_value

    def set(self, key, value, ex):
        self.set_request = (
            key,
            value,
            ex
        )

    def delete(self, key):
        self.deleted_key = key


class UnavailableRedis:
    def get(self, key):
        raise RedisConnectionError(
            "Redis is unavailable"
        )

    def set(self, key, value, ex):
        raise RedisConnectionError(
            "Redis is unavailable"
        )

    def delete(self, key):
        raise RedisConnectionError(
            "Redis is unavailable"
        )


def test_get_ranking_returns_none_when_cache_is_empty():
    redis_client = FakeRedis()
    cache = RedisRankingCache(
        redis_client,
        ttl_seconds=60
    )

    ranking = cache.get_ranking()

    assert redis_client.requested_key == "ranking"
    assert ranking is None


def test_get_ranking_returns_cached_ranking():
    redis_client = FakeRedis(
        '[{"name": "Alice", "score": 120}]'
    )
    cache = RedisRankingCache(
        redis_client,
        ttl_seconds=60
    )

    ranking = cache.get_ranking()

    assert ranking == [
        {
            "name": "Alice",
            "score": 120
        }
    ]


def test_set_ranking_serializes_value_and_sets_ttl():
    redis_client = FakeRedis()
    cache = RedisRankingCache(
        redis_client,
        ttl_seconds=60
    )
    ranking = [
        {
            "name": "Alice",
            "score": 120
        }
    ]

    cache.set_ranking(ranking)

    key, cached_value, ttl = redis_client.set_request

    assert key == "ranking"
    assert json.loads(cached_value) == ranking
    assert ttl == 60


def test_invalidate_ranking_deletes_cache_key():
    redis_client = FakeRedis(
        '[{"name": "Alice", "score": 120}]'
    )
    cache = RedisRankingCache(
        redis_client,
        ttl_seconds=60
    )

    cache.invalidate_ranking()

    assert redis_client.deleted_key == "ranking"


def test_get_ranking_returns_none_when_cache_is_invalid():
    redis_client = FakeRedis(
        "this is not valid json"
    )
    cache = RedisRankingCache(
        redis_client,
        ttl_seconds=60
    )

    ranking = cache.get_ranking()

    assert ranking is None


def test_get_ranking_returns_none_when_redis_is_unavailable():
    cache = RedisRankingCache(
        UnavailableRedis(),
        ttl_seconds=60
    )

    ranking = cache.get_ranking()

    assert ranking is None


def test_set_ranking_ignores_redis_unavailable():
    cache = RedisRankingCache(
        UnavailableRedis(),
        ttl_seconds=60
    )
    ranking = [
        {
            "name": "Alice",
            "score": 120
        }
    ]

    result = cache.set_ranking(ranking)

    assert result is None


def test_invalidate_ranking_ignores_redis_unavailable():
    cache = RedisRankingCache(
        UnavailableRedis(),
        ttl_seconds=60
    )

    result = cache.invalidate_ranking()

    assert result is None
