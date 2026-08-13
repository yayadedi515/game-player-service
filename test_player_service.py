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

if __name__ == "__main__":
    test_basic_operations()
    test_data_isolation()
    test_persistence()
    print("All tests passed")