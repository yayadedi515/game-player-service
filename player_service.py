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