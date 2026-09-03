from typing import Protocol


class RankingCacheProtocol(Protocol):
    def get_ranking(self) -> list[dict] | None:
        ...

    def set_ranking(
            self,
            ranking: list[dict]
    ) -> None:
        ...
