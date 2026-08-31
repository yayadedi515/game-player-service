from typing import Protocol, runtime_checkable

from transfer_result import TransferResult


@runtime_checkable
class PlayerRepositoryProtocol(Protocol):
    def find_player_by_name(self, name: str) -> dict | None:
        ...

    def create_player(self, name: str) -> dict | None:
        ...

    def add_score(self, name: str, score: int) -> dict | None:
        ...

    def get_ranking(self) -> list[dict]:
        ...

    def transfer_score(
            self,
            sender: str,
            receiver: str,
            points: int
    ) -> TransferResult:
        ...

    def delete_player(self, name: str) -> dict | None:
        ...

    def get_transfer_history(
            self,
            limit: int = 20,
            offset: int = 0
    ) -> list[dict]:
        ...
