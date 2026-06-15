import json
import os

def clear():
    print("\033[2J\033[3J\033[H", end="")

gold = "\033[0;33m"
bold = "\033[1m"
underline = "\033[4m"
end = "\033[0m"

os.chdir(os.path.dirname(__file__))
data = json.loads(open("stats.json").read())
cache = json.loads(open("./server/cached_ids.json").read())
users = json.loads(open("./server/users.json").read())

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

user_dict = {}
for user in users:
    user_dict[user["user_id"]] = {
        "username": user["username"],
        "display_name": user["display_name"]
    }

clear()
print(f"{gold}{bold}[Playtime Stat Generator v2.0.0]{end}")
print(f"{bold}Total Server Playtime:{end} {total / 3600:.2f}h\n")

print(f"{bold}Playtime for All Users:{end}")
playtimes = sorted(playtimes.items(), key=lambda item: item[1], reverse=True)
for i, (user, playtime) in enumerate(playtimes, start=1):
    if i == 1:
        print(f"{gold}[#{i}] {user_dict[int(user)]["username"]} ({playtime / 3600:.2f}h){end}")
    elif i == 2:
        print(f"{gold}[#{i}] {user_dict[int(user)]["username"]} ({playtime / 3600:.2f}h){end}")
    elif i == 3:
        print(f"{gold}[#{i}] {user_dict[int(user)]["username"]} ({playtime / 3600:.2f}h){end}")
    print(f"[#{i}] {user_dict[int(user)]["username"]} ({playtime / 3600:.2f}h)")

print(f"\n{bold}Playtime for Top 20 Games:{end}")
game_playtimes = sorted(game_playtimes.items(), key=lambda item: item[1], reverse=True)[:20]
for game, playtime in game_playtimes:
    print(f"{game}: {playtime / 3600:.2f}h")
