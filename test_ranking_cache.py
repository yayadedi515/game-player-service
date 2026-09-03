import json

from ranking_cache import RedisRankingCache


class FakeRedis:
    def __init__(self, cached_value=None):
        self.cached_value = cached_value
        self.requested_key = None
        self.set_request = None

    def get(self, key):
        self.requested_key = key
        return self.cached_value

    def set(self, key, value, ex):
        self.set_request = (
            key,
            value,
            ex
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
