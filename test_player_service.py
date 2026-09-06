from psycopg.errors import RestrictViolation

import pytest
from transfer_result import TransferResult
from player_service import PlayerService
from player_repository_protocol import PlayerRepositoryProtocol
from player_exceptions import (
    InsufficientScoreError,
    InvalidTransferError,
    DuplicatePlayerError,
    PlayerDeletionRestrictedError,
    PlayerNotFoundError,
    UnexpectedTransferResultError
)
from user_exceptions import PermissionDeniedError


PLAYER_OWNER = {
    "user_id": 1,
    "username": "player-owner",
    "created_at": None,
    "role": "user"
}


class FakeRepository:
    def __init__(self):
        self.requested_name = None
        self.created_name = None
        self.ranking_requested = False
        self.score_request = None
        self.deleted_name = None
        self.transfer_request = None
        self.history_request = None
        self.create_player_succeeds = True
        self.add_score_succeeds = True
        self.delete_player_succeeds = True
        self.delete_player_restricted = False
        self.transfer_result = TransferResult.SUCCESS
        self.created_owner_user_id = None
        self.find_player_result = {
            "player_id": 1,
            "name": "Alice",
            "score": 120,
            "created_at": None,
            "owner_user_id": 1
        }

    def find_player_by_name(self, name):
        self.requested_name = name
        return self.find_player_result

    def create_player(
            self,
            name,
            owner_user_id=None
    ):
        self.created_name = name
        self.created_owner_user_id = owner_user_id

        if not self.create_player_succeeds:
            return None

        return {
            "player_id": 2,
            "name": name,
            "score": 0,
            "created_at": None,
            "owner_user_id": owner_user_id
        }

    def get_ranking(self):
        self.ranking_requested = True

        return [
            {
                "player_id": 1,
                "name": "Alice",
                "score": 120,
                "created_at": None
            }
        ]

    def add_score(self, name, points):
        self.score_request = (name, points)

        if not self.add_score_succeeds:
            return None

        return {
            "player_id": 1,
            "name": name,
            "score": 150,
            "created_at": None
        }

    def delete_player(self, name):
        if self.delete_player_restricted:
            raise RestrictViolation(
                "Player is referenced by transfer history"
            )

        self.deleted_name = name

        if not self.delete_player_succeeds:
            return None

        return {
            "player_id": 1,
            "name": name,
            "score": 120,
            "created_at": None,
            "owner_user_id": 1
        }

    def transfer_score(
            self,
            sender,
            receiver,
            points
    ):
        self.transfer_request = (
            sender,
            receiver,
            points
        )

        return self.transfer_result

    def get_transfer_history(
            self,
            limit,
            offset
    ):
        self.history_request = (
            limit,
            offset
        )

        return [
            {
                "transfer_id": 1,
                "sender": "Alice",
                "receiver": "Bob",
                "points": 30,
                "created_at": None
            }
        ]


class FakeRankingCache:
    def __init__(self):
        self.ranking = None
        self.stored_ranking = None
        self.invalidated = False

    def get_ranking(self):
        return self.ranking

    def set_ranking(self, ranking):
        self.stored_ranking = ranking

    def invalidate_ranking(self):
        self.invalidated = True


def test_get_player_uses_repository():
    repository = FakeRepository()
    service = PlayerService(repository)

    player = service.get_player("Alice")

    assert repository.requested_name == "Alice"
    assert player == {
        "player_id": 1,
        "name": "Alice",
        "score": 120,
        "created_at": None,
        "owner_user_id": 1
    }

def test_create_player_uses_repository():
    repository = FakeRepository()
    service = PlayerService(repository)

    player = service.create_player("Diana")

    assert repository.created_name == "Diana"
    assert player["name"] == "Diana"
    assert player["score"] == 0


def test_get_ranking_uses_repository():
    repository = FakeRepository()
    service = PlayerService(repository)

    ranking = service.get_ranking()

    assert repository.ranking_requested is True
    assert ranking == [
        {
            "name": "Alice",
            "score": 120
        }
    ]


def test_add_score_uses_repository():
    repository = FakeRepository()
    service = PlayerService(repository)

    player = service.add_score("Alice", 30)

    assert repository.score_request == (
        "Alice",
        30
    )
    assert player["score"] == 150


def test_add_score_invalidates_ranking_cache():
    repository = FakeRepository()
    ranking_cache = FakeRankingCache()
    service = PlayerService(
        repository,
        ranking_cache=ranking_cache
    )

    service.add_score("Alice", 30)

    assert ranking_cache.invalidated is True


def test_delete_player_uses_repository():
    repository = FakeRepository()
    service = PlayerService(repository)

    player = service.delete_player(
        "Alice",
        PLAYER_OWNER
    )

    assert repository.deleted_name == "Alice"
    assert player["name"] == "Alice"


def test_transfer_score_uses_repository():
    repository = FakeRepository()
    service = PlayerService(repository)

    result = service.transfer_score(
        "Alice",
        "Bob",
        30,
        PLAYER_OWNER
    )

    assert repository.transfer_request == (
        "Alice",
        "Bob",
        30
    )
    assert result == {
        "sender": "Alice",
        "receiver": "Bob",
        "points": 30
    }


def test_get_transfer_history_uses_repository():
    repository = FakeRepository()
    service = PlayerService(repository)

    history = service.get_transfer_history(
        limit=10,
        offset=20
    )

    assert repository.history_request == (
        10,
        20
    )
    assert history[0]["transfer_id"] == 1


def test_get_missing_player_raises_player_not_found():
    repository = FakeRepository()
    repository.find_player_result = None
    service = PlayerService(repository)

    with pytest.raises(PlayerNotFoundError):
        service.get_player("Cindy")


def test_create_duplicate_player_raises_duplicate_player():
    repository = FakeRepository()
    repository.create_player_succeeds = False
    service = PlayerService(repository)

    with pytest.raises(DuplicatePlayerError):
        service.create_player("Alice")


def test_add_score_missing_player_raises_player_not_found():
    repository = FakeRepository()
    repository.add_score_succeeds = False
    service = PlayerService(repository)

    with pytest.raises(PlayerNotFoundError):
        service.add_score("Cindy", 30)


def test_delete_missing_player_raises_player_not_found():
    repository = FakeRepository()
    repository.find_player_result = None

    service = PlayerService(repository)

    with pytest.raises(PlayerNotFoundError):
        service.delete_player(
            "Cindy",
            PLAYER_OWNER
        )

    assert repository.deleted_name is None


def test_delete_restricted_player_raises_business_error():
    repository = FakeRepository()
    repository.delete_player_restricted = True
    service = PlayerService(repository)

    with pytest.raises(PlayerDeletionRestrictedError):
        service.delete_player(
            "Alice",
            PLAYER_OWNER
        )


@pytest.mark.parametrize(
    ("repository_result", "expected_error"),
    [
        (
            TransferResult.PLAYER_NOT_FOUND,
            PlayerNotFoundError
        ),
        (
            TransferResult.INSUFFICIENT_SCORE,
            InsufficientScoreError
        ),
        (
            TransferResult.INVALID_REQUEST,
            InvalidTransferError
        ),
    ]
)
def test_transfer_score_converts_results_to_business_errors(
        repository_result,
        expected_error
):
    repository = FakeRepository()
    repository.transfer_result = repository_result
    service = PlayerService(repository)

    with pytest.raises(expected_error):
        service.transfer_score(
            "Alice",
            "Bob",
            30,
            PLAYER_OWNER
        )


def test_transfer_score_unexpected_result_raises_error():
    repository = FakeRepository()
    repository.transfer_result = object()
    service = PlayerService(repository)

    with pytest.raises(UnexpectedTransferResultError):
        service.transfer_score(
            "Alice",
            "Bob",
            30,
            PLAYER_OWNER
        )


def test_fake_repository_satisfies_repository_protocol():
    repository = FakeRepository()

    assert isinstance(
        repository,
        PlayerRepositoryProtocol
    )


def test_get_ranking_returns_cache_without_using_repository():
    repository = FakeRepository()
    cache = FakeRankingCache()
    cache.ranking = [
        {
            "name": "Cached Alice",
            "score": 999
        }
    ]
    service = PlayerService(
        repository,
        ranking_cache=cache
    )

    ranking = service.get_ranking()

    assert ranking == [
        {
            "name": "Cached Alice",
            "score": 999
        }
    ]
    assert repository.ranking_requested is False


def test_get_ranking_stores_repository_result_in_cache():
    repository = FakeRepository()
    cache = FakeRankingCache()
    service = PlayerService(
        repository,
        ranking_cache=cache
    )

    ranking = service.get_ranking()

    assert repository.ranking_requested is True
    assert ranking == [
        {
            "name": "Alice",
            "score": 120
        }
    ]
    assert cache.stored_ranking == ranking


def test_create_player_invalidates_ranking_cache():
    repository = FakeRepository()
    ranking_cache = FakeRankingCache()
    service = PlayerService(
        repository,
        ranking_cache=ranking_cache
    )

    service.create_player("Diana")

    assert ranking_cache.invalidated is True


def test_delete_player_invalidates_ranking_cache():
    repository = FakeRepository()
    ranking_cache = FakeRankingCache()
    service = PlayerService(
        repository,
        ranking_cache=ranking_cache
    )

    service.delete_player(
        "Alice",
        PLAYER_OWNER
    )

    assert ranking_cache.invalidated is True


def test_transfer_score_invalidates_ranking_cache():
    repository = FakeRepository()
    ranking_cache = FakeRankingCache()
    service = PlayerService(
        repository,
        ranking_cache=ranking_cache
    )

    service.transfer_score(
        "Alice",
        "Bob",
        30,
        PLAYER_OWNER
    )

    assert ranking_cache.invalidated is True


def test_failed_transfer_does_not_invalidate_ranking_cache():
    repository = FakeRepository()
    repository.transfer_result = (
        TransferResult.INSUFFICIENT_SCORE
    )
    ranking_cache = FakeRankingCache()

    service = PlayerService(
        repository,
        ranking_cache=ranking_cache
    )

    with pytest.raises(InsufficientScoreError):
        service.transfer_score(
            "Alice",
            "Bob",
            30,
            PLAYER_OWNER
        )

    assert ranking_cache.invalidated is False


def test_create_player_assigns_authenticated_user_as_owner():
    repository = FakeRepository()
    service = PlayerService(repository)

    player = service.create_player(
        "Diana",
        owner_user_id=7
    )

    assert repository.created_name == "Diana"
    assert repository.created_owner_user_id == 7
    assert player["owner_user_id"] == 7


def test_regular_user_cannot_delete_another_users_player():
    repository = FakeRepository()
    repository.find_player_result[
        "owner_user_id"
    ] = 2

    service = PlayerService(repository)

    current_user = {
        "user_id": 1,
        "username": "regular-user",
        "created_at": None,
        "role": "user"
    }

    with pytest.raises(PermissionDeniedError):
        service.delete_player(
            "Alice",
            current_user
        )

    assert repository.deleted_name is None


def test_player_owner_can_delete_own_player():
    repository = FakeRepository()
    repository.find_player_result[
        "owner_user_id"
    ] = 1

    service = PlayerService(repository)

    current_user = {
        "user_id": 1,
        "username": "player-owner",
        "created_at": None,
        "role": "user"
    }

    player = service.delete_player(
        "Alice",
        current_user
    )

    assert repository.deleted_name == "Alice"
    assert player["name"] == "Alice"


def test_admin_can_delete_another_users_player():
    repository = FakeRepository()
    repository.find_player_result[
        "owner_user_id"
    ] = 2

    service = PlayerService(repository)

    current_user = {
        "user_id": 1,
        "username": "admin-user",
        "created_at": None,
        "role": "admin"
    }

    player = service.delete_player(
        "Alice",
        current_user
    )

    assert repository.deleted_name == "Alice"
    assert player["name"] == "Alice"


def test_regular_user_cannot_transfer_from_another_users_player():
    repository = FakeRepository()
    repository.find_player_result[
        "owner_user_id"
    ] = 2

    service = PlayerService(repository)

    current_user = {
        "user_id": 1,
        "username": "regular-user",
        "created_at": None,
        "role": "user"
    }

    with pytest.raises(PermissionDeniedError):
        service.transfer_score(
            "Alice",
            "Bob",
            30,
            current_user
        )

    assert repository.transfer_request is None


def test_player_owner_can_transfer_from_own_player():
    repository = FakeRepository()
    repository.find_player_result[
        "owner_user_id"
    ] = PLAYER_OWNER["user_id"]

    service = PlayerService(repository)

    result = service.transfer_score(
        "Alice",
        "Bob",
        30,
        PLAYER_OWNER
    )

    assert repository.transfer_request == (
        "Alice",
        "Bob",
        30
    )
    assert result == {
        "sender": "Alice",
        "receiver": "Bob",
        "points": 30
    }


def test_admin_cannot_transfer_from_another_users_player():
    repository = FakeRepository()
    repository.find_player_result[
        "owner_user_id"
    ] = 2

    service = PlayerService(repository)

    admin_user = {
        "user_id": 1,
        "username": "admin-user",
        "created_at": None,
        "role": "admin"
    }

    with pytest.raises(PermissionDeniedError):
        service.transfer_score(
            "Alice",
            "Bob",
            30,
            admin_user
        )

    assert repository.transfer_request is None
