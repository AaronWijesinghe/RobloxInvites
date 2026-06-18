import json
import os

def clear():
    print("\033[2J\033[3J\033[H", end="")

gold = "\033[0;33m"
silver = "\033[38;5;250m"
bronze = "\033[38;5;173m"
bold = "\033[1m"
underline = "\033[4m"
end = "\033[0m"

os.chdir(os.path.dirname(__file__))
data = json.loads(open("./server/stats.json").read())
cache = json.loads(open("./server/cached_ids.json").read())
users = json.loads(open("./server/users.json").read())

def leaderboard(string, pos):
    if pos == 1:
        return f"{gold}{string}{end}"
    elif pos == 2:
        return f"{silver}{string}{end}"
    elif pos == 3:
        return f"{bronze}{string}{end}"
    else:
        return string

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

def generate_stats(playtimes, game_playtimes):
    clear()
    print(f"{gold}{bold}[Server Leaderboard]{end}")
    print(f"{bold}{underline}Total Server Playtime:{end} {total / 3600:.2f}h\n")

    print(f"{bold}Playtime for Top 20 Users:{end}")
    playtimes = sorted(playtimes.items(), key=lambda item: item[1], reverse=True)[:20]
    for i, (user, playtime) in enumerate(playtimes, start=1):
        print(leaderboard(f"[#{i}] {user_dict[int(user)]["username"]} ({playtime / 3600:.2f}h)", i))

    print(f"\n{bold}Playtime for Top 20 Games:{end}")
    game_playtimes = sorted(game_playtimes.items(), key=lambda item: item[1], reverse=True)[:20]
    for i, (game, playtime) in enumerate(game_playtimes, start=1):
        print(leaderboard(f"[#{i}] {game}: {playtime / 3600:.2f}h", i))
    input("\nPress ENTER to return to the main menu. ")

def save_data(total, playtimes, game_playtimes):
    playtimes_diff = {}
    game_playtimes_diff = {}
    total_diff = 0
    if len(data["weeks"]) > 0:
        total_diff = data["weeks"][len(data["weeks"]) - 1]["total"] - data["weeks"][len(data["weeks"]) - 2]["total"]
        playtimes_new = data["weeks"][len(data["weeks"]) - 1]["playtimes"]
        playtimes_old = data["weeks"][len(data["weeks"]) - 2]["playtimes"]
        game_playtimes_new = data["weeks"][len(data["weeks"]) - 1]["game_playtimes"]
        game_playtimes_old = data["weeks"][len(data["weeks"]) - 2]["game_playtimes"]
        for name in playtimes_new.keys():
            if name in playtimes_old:
                playtimes_diff[name] = playtimes_new[name] - playtimes_old[name]
            else:
                playtimes_diff[name] = playtimes_new[name]
        for name in game_playtimes_new.keys():
            if name in game_playtimes_old:
                game_playtimes_diff[name] = game_playtimes_new[name] - game_playtimes_old[name]
            else:
                game_playtimes_diff[name] = game_playtimes_new[name]
    else:
        playtimes_diff = playtimes
        game_playtimes_diff = game_playtimes
        total_diff = total

    data["weeks"] += [{
        "total": total,
        "playtimes": playtimes,
        "game_playtimes": game_playtimes,
        "total_diff": total_diff,
        "playtimes_diff": playtimes_diff,
        "game_playtimes_diff": game_playtimes_diff
    }]
    open("./server/stat_summarizer.json", "w").write(json.dumps(data, indent=2))

def generate_weekly_stats():
    total = data["weeks"][len(data["weeks"]) - 1]["total_diff"]
    playtimes = data["weeks"][len(data["weeks"]) - 1]["playtimes_diff"]
    game_playtimes = data["weeks"][len(data["weeks"]) - 1]["game_playtimes_diff"]

    clear()
    print(f"{gold}{bold}[Weekly Server Leaderboard]{end}")
    print(f"{bold}{underline}Total Server Playtime This Week:{end} {total / 3600:.2f}h\n")

    print(f"{bold}Weekly Playtime for Top 20 Users:{end}")
    playtimes = sorted(playtimes.items(), key=lambda item: item[1], reverse=True)[:20]
    for i, (user, playtime) in enumerate(playtimes, start=1):
        print(leaderboard(f"[#{i}] {user_dict[int(user)]["username"]} ({playtime / 3600:.2f}h)", i))

    print(f"\n{bold}Weekly Playtime for Top 20 Games:{end}")
    game_playtimes = sorted(game_playtimes.items(), key=lambda item: item[1], reverse=True)[:20]
    for i, (game, playtime) in enumerate(game_playtimes, start=1):
        print(leaderboard(f"[#{i}] {game}: {playtime / 3600:.2f}h", i))
    input("\nPress ENTER to return to the main menu. ")

if os.path.exists("./server/stat_summarizer.json"):
    data = json.loads(open("./server/stat_summarizer.json", "r").read())
else:
    data = {
        "version": 1,
        "weeks": []
    }
    open("./server/stat_summarizer.json", "w").write(json.dumps(data, indent=2))

while True:
    clear()
    print(f"{gold}{bold}[Playtime Stat Generator v4.1.0]{end}")
    print("Supports Roblox Invites v5.0.0 - v5.0.1")

    print("\nCommands:")
    print("    - /lb - Generates leaderboards for all data ('') or for the current week ('weekly')")
    print("    - /save - Saves playtime data to /server/stat_summarization.json, and diffs the hours from the previous week (if possible)")

    command = input("\nEnter a command ('/lb'): ").lower().strip()

    args = command.split(" ")[1:]
    if command.startswith("/lb"):
        if len(args) == 0:
            generate_stats(playtimes, game_playtimes)
            continue
        if args[0] == "weekly":
            generate_weekly_stats()
    elif command == "/save":
        save_data(total, playtimes, game_playtimes)