from transfer_result import TransferResult
from player_service import PlayerService


class FakeRepository:
    def __init__(self):
        self.requested_name = None
        self.created_name = None
        self.ranking_requested = False
        self.score_request = None
        self.deleted_name = None
        self.transfer_request = None
        self.history_request = None

    def find_player_by_name(self, name):
        self.requested_name = name

        return {
            "player_id": 1,
            "name": "Alice",
            "score": 120,
            "created_at": None
        }

    def create_player(self, name):
        self.created_name = name

        return {
            "player_id": 2,
            "name": name,
            "score": 0,
            "created_at": None
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

        return {
            "player_id": 1,
            "name": name,
            "score": 150,
            "created_at": None
        }

    def delete_player(self, name):
        self.deleted_name = name

        return {
            "player_id": 1,
            "name": name,
            "score": 120,
            "created_at": None
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

        return TransferResult.SUCCESS

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

def test_get_player_uses_repository():
    repository = FakeRepository()
    service = PlayerService(repository)

    player = service.get_player("Alice")

    assert repository.requested_name == "Alice"
    assert player == {
        "player_id": 1,
        "name": "Alice",
        "score": 120,
        "created_at": None
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
    assert ranking[0]["name"] == "Alice"


def test_add_score_uses_repository():
    repository = FakeRepository()
    service = PlayerService(repository)

    player = service.add_score("Alice", 30)

    assert repository.score_request == (
        "Alice",
        30
    )
    assert player["score"] == 150


def test_delete_player_uses_repository():
    repository = FakeRepository()
    service = PlayerService(repository)

    player = service.delete_player("Alice")

    assert repository.deleted_name == "Alice"
    assert player["name"] == "Alice"


def test_transfer_score_uses_repository():
    repository = FakeRepository()
    service = PlayerService(repository)

    result = service.transfer_score(
        "Alice",
        "Bob",
        30
    )

    assert repository.transfer_request == (
        "Alice",
        "Bob",
        30
    )
    assert result is TransferResult.SUCCESS


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