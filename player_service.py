import json
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

    except FileNotFoundError:
        return {}
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