import json

from redis.exceptions import RedisError


class RedisRankingCache:
    CACHE_KEY = "ranking"

    def __init__(
            self,
            redis_client,
            ttl_seconds: int
    ):
        self.redis_client = redis_client
        self.ttl_seconds = ttl_seconds

    def get_ranking(self) -> list[dict] | None:
        try:
            cached_ranking = self.redis_client.get(
                self.CACHE_KEY
            )

            if cached_ranking is None:
                return None

            return json.loads(cached_ranking)
        except (
                RedisError,
                json.JSONDecodeError
        ):
            return None

    def set_ranking(
            self,
            ranking: list[dict]
    ) -> None:
        try:
            self.redis_client.set(
                self.CACHE_KEY,
                json.dumps(ranking),
                ex=self.ttl_seconds
            )
        except RedisError:
            return None

    def invalidate_ranking(self) -> None:
        try:
            self.redis_client.delete(
                self.CACHE_KEY
            )
        except RedisError:
            return None
