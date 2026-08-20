import json
import copy
def add_player(players, name):
    name=name.strip()
    if name in players or name == "":
        return False
    players[name] = 0
    return True

def add_score(players, name, score):
    name=name.strip()
    if name not in players or score < 0:
        return False
    players[name] = players[name] + score
    return True

def get_ranking(players):
    ranking=sorted(players.items(), key=lambda x: (-x[1], x[0]))
    return ranking

def save_players(players, filename):
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(
                players,
                file,
                ensure_ascii = False,
                indent = 2
            )

    except OSError:
        return False
    else:
        return True

def load_players(filename):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            loaded_players = json.load(file)

    except (OSError, json.JSONDecodeError):
        return None

    else:
        return loaded_players

# Day 17
def get_score(players, name):
    name = name.strip()
    if name not in players or name == "":
        return None
    return players[name]
def remove_player(players, name):
    name = name.strip()
    if name not in players or name == "":
        return False
    del players[name]
    return True

def transfer_score(players, sender, receiver, points):
    # 1. 清理两个名字
    # 2. 一次性完成所有合法性检查
    # 3. 检查全部通过后，才修改双方积分
    # 4. 成功返回True，失败返回False
    sender=sender.strip()
    receiver=receiver.strip()
    if (
        not sender
        or not receiver
        or sender == receiver
        or sender not in players
        or receiver not in players
        or points <= 0
        or players[sender] < points
    ):
        return False
    players[sender] -= points
    players[receiver] += points
    return True

class PlayerService:
    def __init__(self, initial_players=None):
        if initial_players is None:
            self.players = {}
        else:
            self.players = copy.deepcopy(initial_players)
        self.transfer_history = []
    def add_player(self, name):
        return add_player(self.players, name)
    def add_score(self, name, score):
        return add_score(self.players, name, score)
    def get_score(self, name):
        return get_score(self.players, name)
    def remove_player(self, name):
        return remove_player(self.players, name)
    def get_ranking(self):
        return get_ranking(self.players)
    def save(self, filename):
        return save_players(self.players, filename)

    def load(self, filename):
        loaded_players = load_players(filename)

        if loaded_players is None:
            return False

        if not isinstance(loaded_players, dict):
            return False

        self.players = loaded_players
        return True
    def transfer_score(self, sender, receiver, points):
        sender = sender.strip()
        receiver = receiver.strip()
        success = transfer_score(
            self.players,
            sender,
            receiver,
            points
        )

        if success:
            self.transfer_history.append({
                "sender": sender,
                "receiver": receiver,
                "points": points
            })
        return success


if __name__ == "__main__":  #测试~~
    players = {}
    print(add_player(players, "Alice"))
    print(add_player(players, "Alice"))
    print(add_player(players, "Bob"))
    print(add_score(players, "Alice", 120))
    print(add_score(players, "Bob", 90))
    print(add_score(players, "Cindy", 50))
    print(add_score(players, "Bob", -10))
    print(get_ranking(players))

    print(add_player(players, "  Charlie  "))
    print(add_score(players, " Charlie ", 90))
    print(add_player(players, "   "))
    print(get_ranking(players))

    print(save_players(players, "players.json"))

    loaded_players = load_players("players.json")
    print(loaded_players)
    print(get_ranking(loaded_players))

    print(load_players("missing.json"))

    # Day 17
    print("17====================")
    test_players = {
        "Alice": 120,
        "Bob": 90,
        "Charlie": 90
    }

    print(get_score(test_players, " Alice "))
    print(get_score(test_players, "Cindy"))
    print(get_score(test_players, "   "))

    print(remove_player(test_players, " Bob "))
    print(remove_player(test_players, "Bob"))
    print(remove_player(test_players, "   "))

    print(test_players)
    edge_players = {"": 999}

    print(get_score(edge_players, "   "))
    print(remove_player(edge_players, "   "))
    print(edge_players)

    print("18====================")
    initial_players = {
        "Alice": 120
    }

    service = PlayerService(initial_players)

    print(service.add_player(" Bob "))
    print(service.add_score("Bob", 90))
    print(service.get_score(" Alice "))
    print(service.get_ranking())
    print(service.remove_player("Alice"))
    print(service.get_ranking())
    print(initial_players)

    original = {"Alice": 120}

    service_a = PlayerService(original)
    service_b = PlayerService(original)
    print("XXX")
    service_a.add_player("Bob")

    print(service_a.players)
    print(service_b.players)
    print(original)