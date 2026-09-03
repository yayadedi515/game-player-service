import json


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
        cached_ranking = self.redis_client.get(
            self.CACHE_KEY
        )

        if cached_ranking is None:
            return None

        return json.loads(cached_ranking)

    def set_ranking(
            self,
            ranking: list[dict]
    ) -> None:
        self.redis_client.set(
            self.CACHE_KEY,
            json.dumps(ranking),
            ex=self.ttl_seconds
        )