import json
import os

os.chdir(os.path.dirname(__file__))
data = json.loads(open("stats.json").read())
cache = json.loads(open("./server/cached_ids.json").read())

total = 0
playtimes = {}
game_playtimes = {}
id_to_name = {}
for c in cache["caches"].items():
    id_to_name[str(c[1]["root_place_id"])] = c[1]["name"]
for user in data:
    playtimes[user] = 0
    for game in data[user]["games_played"]:
        if str(game) in data[user]["games_playtime"]:
            if str(game) not in id_to_name:
                id_to_name[str(game)] = str(game)
            if id_to_name[str(game)] not in game_playtimes:
                game_playtimes[id_to_name[str(game)]] = 0
            game_playtimes[id_to_name[str(game)]] += data[user]["games_playtime"][
                str(game)
            ]["playtime"]
            total += data[user]["games_playtime"][str(game)]["playtime"]
            playtimes[user] += data[user]["games_playtime"][str(game)]["playtime"]

print("Playtime Stat Generator v1.0.0")
print(f"Total Server Playtime: {total / 3600:.2f}h\n")

print("Playtime for All Users:")
playtimes = sorted(playtimes.items(), key=lambda item: item[1], reverse=True)
for user, playtime in playtimes:
    print(
        f"{user}: Calculated - {playtime / 3600:.2f}h | Logged - {data[user]['total_playtime'] / 3600:.2f}h (DIFF: {(playtime / 3600 - data[user]['total_playtime'] / 3600):.2f}h)"
    )

print("\nPlaytime for Top 20 Games:")
game_playtimes = sorted(game_playtimes.items(), key=lambda item: item[1], reverse=True)[
    :20
]
for game, playtime in game_playtimes:
    print(f"{game}: {playtime / 3600:.2f}h")
