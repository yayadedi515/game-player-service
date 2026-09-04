from psycopg.errors import (
    ForeignKeyViolation,
    RestrictViolation,
)

from transfer_result import TransferResult
from ranking_cache_protocol import RankingCacheProtocol
from player_repository_protocol import PlayerRepositoryProtocol
from player_exceptions import (
    InsufficientScoreError,
    InvalidTransferError,
    UnexpectedTransferResultError,
    PlayerDeletionRestrictedError,
    DuplicatePlayerError,
    PlayerNotFoundError,
)


class PlayerService:
    def __init__(
            self,
            repository: PlayerRepositoryProtocol,
            ranking_cache: RankingCacheProtocol | None = None
    ):
        self.repository = repository
        self.ranking_cache = ranking_cache

    def get_player(self, name):
        player = self.repository.find_player_by_name(name)

        if player is None:
            raise PlayerNotFoundError

        return player

    def create_player(self, name):
        player = self.repository.create_player(name)

        if player is None:
            raise DuplicatePlayerError

        if self.ranking_cache is not None:
            self.ranking_cache.invalidate_ranking()

        return player

    def get_ranking(self):
        if self.ranking_cache is not None:
            cached_ranking = (
                self.ranking_cache.get_ranking()
            )

            if cached_ranking is not None:
                return cached_ranking

        players = self.repository.get_ranking()

        ranking = [
            {
                "name": player["name"],
                "score": player["score"]
            }
            for player in players
        ]

        if self.ranking_cache is not None:
            self.ranking_cache.set_ranking(ranking)

        return ranking

    def add_score(self, name, points):
        player = self.repository.add_score(name, points)

        if player is None:
            raise PlayerNotFoundError

        if self.ranking_cache is not None:
            self.ranking_cache.invalidate_ranking()

        return player

    def delete_player(self, name):
        try:
            player = self.repository.delete_player(name)
        except (
                ForeignKeyViolation,
                RestrictViolation
        ) as error:
            raise PlayerDeletionRestrictedError from error

        if player is None:
            raise PlayerNotFoundError

        if self.ranking_cache is not None:
            self.ranking_cache.invalidate_ranking()

        return player

    def transfer_score(
            self,
            sender,
            receiver,
            points
    ):
        cleaned_sender = sender.strip()
        cleaned_receiver = receiver.strip()

        result = self.repository.transfer_score(
            cleaned_sender,
            cleaned_receiver,
            points
        )

        if result is TransferResult.SUCCESS:
            if self.ranking_cache is not None:
                self.ranking_cache.invalidate_ranking()

            return {
                "sender": cleaned_sender,
                "receiver": cleaned_receiver,
                "points": points
            }

        if result is TransferResult.PLAYER_NOT_FOUND:
            raise PlayerNotFoundError

        if result is TransferResult.INSUFFICIENT_SCORE:
            raise InsufficientScoreError

        if result is TransferResult.INVALID_REQUEST:
            raise InvalidTransferError

        raise UnexpectedTransferResultError

    def get_transfer_history(
            self,
            limit=20,
            offset=0
    ):
        return self.repository.get_transfer_history(
            limit=limit,
            offset=offset
        )
