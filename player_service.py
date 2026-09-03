from psycopg.errors import (
    ForeignKeyViolation,
    RestrictViolation,
)

from transfer_result import TransferResult
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
            repository: PlayerRepositoryProtocol
    ):
        self.repository = repository

    def get_player(self, name):
        player = self.repository.find_player_by_name(name)

        if player is None:
            raise PlayerNotFoundError

        return player

    def create_player(self, name):
        player = self.repository.create_player(name)

        if player is None:
            raise DuplicatePlayerError

        return player

    def get_ranking(self):
        return self.repository.get_ranking()

    def add_score(self, name, points):
        player = self.repository.add_score(name, points)

        if player is None:
            raise PlayerNotFoundError

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
