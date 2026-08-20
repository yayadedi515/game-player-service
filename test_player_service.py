from player_service import PlayerService
from pathlib import Path
from tempfile import TemporaryDirectory

def test_basic_operations():
    service = PlayerService()

    assert service.add_player("Alice") is True
    assert service.add_player("Alice") is False
    assert service.add_player("   ") is False

    assert service.add_score("Alice", 120) is True
    assert service.add_score("Bob", 50) is False
    assert service.add_score("Alice", -10) is False

    assert service.get_score(" Alice ") == 120
    assert service.get_score("Bob") is None

    assert service.get_ranking() == [("Alice", 120)]

    assert service.remove_player("Alice") is True
    assert service.remove_player("Alice") is False

def test_data_isolation():
    original = {
        "Alice": {
            "score": 120,
            "items": []
        }
    }
    service_a = PlayerService(original)
    service_b = PlayerService(original)
    service_a.players["Alice"]["items"].append("Sword")
    assert service_a.players["Alice"]["items"] == ["Sword"]
    assert service_b.players["Alice"]["items"] == []
    assert original["Alice"]["items"] == []

def test_persistence():
    service_a = PlayerService({
        "Alice": 120,
        "Bob": 90
    })

    with TemporaryDirectory() as temp_directory:
        filename = Path(temp_directory) / "players.json"

        assert service_a.save(filename) is True

        service_b = PlayerService()
        assert service_b.load(filename) is True
        assert service_b.players == {
            "Alice": 120,
            "Bob": 90
        }
        assert service_b.players is not service_a.players

        service_c = PlayerService({"Charlie": 50})
        missing_file = Path(temp_directory) / "missing.json"

        assert service_c.load(missing_file) is False
        assert service_c.players == {"Charlie": 50}


def test_transfer_score_success():
    service = PlayerService({
        "Alice": 100,
        "Bob": 20
    })

    result = service.transfer_score(
        " Alice ",
        " Bob ",
        30
    )

    assert result is True
    assert service.players == {
        "Alice": 70,
        "Bob": 50
    }

def test_transfer_score_failures():
    service = PlayerService({
        "Alice": 100,
        "Bob": 20
    })

    invalid_cases = [
        ("Cindy", "Bob", 10),     # 发送者不存在
        ("Alice", "Cindy", 10),   # 接收者不存在
        ("Alice", "Alice", 10),   # 给自己转账
        ("Alice", "Bob", 0),      # 数量为0
        ("Alice", "Bob", -10),    # 数量为负
        ("Alice", "Bob", 101),    # 余额不足
        ("   ", "Bob", 10),       # 发送者为空
        ("Alice", "   ", 10),     # 接收者为空
    ]

    for sender, receiver, points in invalid_cases:
        before = service.players.copy()

        result = service.transfer_score(
            sender,
            receiver,
            points
        )

        assert result is False, (
            f"Unexpected success: "
            f"sender={sender!r}, "
            f"receiver={receiver!r}, "
            f"points={points}"
        )
        assert service.players == before

def test_transfer_all_score():
    service = PlayerService({
        "Alice": 100,
        "Bob": 20
    })

    assert service.transfer_score(
        "Alice",
        "Bob",
        100
    ) is True

    assert service.players == {
        "Alice": 0,
        "Bob": 120
    }

def test_transfer_history():
    service = PlayerService({
        "Alice": 100,
        "Bob": 20
    })

    assert service.transfer_history == []

    assert service.transfer_score(
        " Alice ",
        " Bob ",
        30
    ) is True

    assert service.transfer_history == [
        {
            "sender": "Alice",
            "receiver": "Bob",
            "points": 30
        }
    ]

    assert service.transfer_score(
        "Alice",
        "Bob",
        100
    ) is False

    assert len(service.transfer_history) == 1

if __name__ == "__main__":
    test_basic_operations()
    test_data_isolation()
    test_persistence()
    test_transfer_score_success()
    test_transfer_score_failures()
    test_transfer_all_score()
    test_transfer_history()

    print("All tests passed")