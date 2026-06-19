import json
import os
import time
from datetime import datetime

gold = "\033[0;33m"
silver = "\033[38;5;250m"
bronze = "\033[38;5;173m"
bold = "\033[1m"
underline = "\033[4m"
end = "\033[0m"

os.chdir(os.path.dirname(__file__))
users = json.loads(open("./server/users.json").read())

user_dict = {}
for user in users:
    user_dict[user["user_id"]] = {
        "username": user["username"],
        "display_name": user["display_name"]
    }

def clear():
    print("\033[2J\033[3J\033[H", end="")

def format_leaderboard(string, pos):
    if pos == 1:
        return f"{gold}{string}{end}"
    elif pos == 2:
        return f"{silver}{string}{end}"
    elif pos == 3:
        return f"{bronze}{string}{end}"
    else:
        return string

def get_latest_data():
    total = 0
    playtimes = {}
    game_playtimes = {}
    stats = json.loads(open("./server/stats.json").read())
    for user in stats:
        playtimes[user] = 0
        for game in stats[user]["games_playtime"].keys():
            if game not in game_playtimes:
                game_playtimes[game] = 0
            game_playtimes[game] += stats[user]["games_playtime"][game]["playtime"]
            total += stats[user]["games_playtime"][game]["playtime"]
            playtimes[user] += stats[user]["games_playtime"][game]["playtime"]
    return (total, playtimes, game_playtimes)

def game_select(query):
    cache = json.loads(open("./server/cached_ids.json").read())["caches"]
    game_cache = {}
    for universe_id in cache.keys():
        game_cache[cache[universe_id]["name"]] = cache[universe_id]["root_place_id"]

    games = list(game_cache.keys())
    valid_games = []
    for game in games:
        if query.lower() in game.lower():
            valid_games += [game]
    if len(valid_games) > 0:
        return game_cache[valid_games[0]]
    else:
        return None

def generate_stats(lb_type, total, playtimes, game_playtimes):
    global cache
    titles = {
        "weekly": "[Weekly]",
        "all": "[All]",
        "range": "[Range]"
    }

    clear()
    print(f"{gold}{bold}[Server Leaderboard] {titles[lb_type]}{end}")
    print(f"{bold}{underline}Total Server Playtime:{end} {total / 3600:.2f}h\n")

    print(f"{bold}Playtime for Top 20 Users:{end}")
    playtimes = sorted(playtimes.items(), key=lambda item: item[1], reverse=True)[:20]
    for i, (user, playtime) in enumerate(playtimes, start=1):
        print(format_leaderboard(f"[#{i}] {user_dict[int(user)]["display_name"]} ({playtime / 3600:.2f}h)", i))

    print(f"\n{bold}Playtime for Top 20 Games:{end}")
    game_playtimes = sorted(game_playtimes.items(), key=lambda item: item[1], reverse=True)[:20]
    for i, (game, playtime) in enumerate(game_playtimes, start=1):
        universe_id = cache["indexes"][str(game)]
        name = cache["caches"][str(universe_id)]["name"]
        print(format_leaderboard(f"[#{i}] {name}: {playtime / 3600:.2f}h", i))
    input("\nPress ENTER to return to the main menu. ")

def generate_game_stats(game):
    global cache

    clear()
    if game == None:
        print(f"{gold}{bold}[Error]{end}")
        input("This game couldn't be found.")
        return

    total = 0
    playtimes = {}
    stats = data["weeks"][len(data["weeks"]) - 1]["stats"]
    for user_id, statistics in stats.items():
        if str(game) in statistics["games_playtime"]:
            playtimes[str(user_id)] = statistics["games_playtime"][str(game)]["playtime"]
            total += statistics["games_playtime"][str(game)]["playtime"]

    universe_id = cache["indexes"][str(game)]
    name = cache["caches"][str(universe_id)]["name"]
    print(f"{gold}{bold}[Leaderboard for {name}]{end}")
    print(f"{bold}{underline}Total Server Playtime:{end} {total / 3600:.2f}h\n")

    print(f"{bold}Playtime for Top 20 Users:{end}")
    playtimes = sorted(playtimes.items(), key=lambda item: item[1], reverse=True)[:20]
    for i, (user, playtime) in enumerate(playtimes, start=1):
        print(format_leaderboard(f"[#{i}] {user_dict[int(user)]["display_name"]} ({playtime / 3600:.2f}h)", i))
    input("\nPress ENTER to return to the main menu. ")

def save_playtime_data():
    stats = json.loads(open("./server/stats.json").read())
    total, playtimes, game_playtimes = get_latest_data()

    data["weeks"] += [{
        "total": total,
        "playtimes": playtimes,
        "game_playtimes": game_playtimes,
        "stats": stats
    }]
    open("./server/playtime_tools.json", "w").write(json.dumps(data, indent=2))

def get_diff(week_1, week_2):
    playtimes_diff = {}
    game_playtimes_diff = {}

    total_diff = data["weeks"][week_2]["total"] - data["weeks"][week_1]["total"]
    playtimes_new = data["weeks"][week_2]["playtimes"]
    playtimes_old = data["weeks"][week_1]["playtimes"]
    game_playtimes_new = data["weeks"][week_2]["game_playtimes"]
    game_playtimes_old = data["weeks"][week_1]["game_playtimes"]
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
    
    return {"playtimes": playtimes_diff, "game_playtimes": game_playtimes_diff, "total": total_diff}

def live_stats():
    global cache

    while True:
        total, playtimes, game_playtimes = get_latest_data()
        timestamp_date = datetime.now().strftime("%m-%d-%Y")
        timestamp_time = datetime.now().strftime("%H:%M:%S")

        clear()
        print(f"{gold}{bold}[Server Leaderboard] [Live]{end}")
        print("Your time is only counted after you leave a game.")
        print(f"Current Date/Time: {timestamp_time} @ {timestamp_date}")
        print(f"{bold}{underline}Total Server Playtime:{end} {total / 3600:.2f}h\n")

        print(f"{bold}Playtime for Top 20 Users:{end}")
        playtimes = sorted(playtimes.items(), key=lambda item: item[1], reverse=True)[:20]
        for i, (user, playtime) in enumerate(playtimes, start=1):
            print(format_leaderboard(f"[#{i}] {user_dict[int(user)]["display_name"]} ({playtime / 3600:.2f}h)", i))

        print(f"\n{bold}Playtime for Top 20 Games:{end}")
        game_playtimes = sorted(game_playtimes.items(), key=lambda item: item[1], reverse=True)[:20]
        for i, (game, playtime) in enumerate(game_playtimes, start=1):
            universe_id = cache["indexes"][str(game)]
            name = cache["caches"][str(universe_id)]["name"]
            print(format_leaderboard(f"[#{i}] {name}: {playtime / 3600:.2f}h", i))
        time.sleep(5)

def live_game_stats(game):
    global cache

    if game == None:
        print(f"{gold}{bold}[Error]{end}")
        input("This game couldn't be found.")
        return
    universe_id = cache["indexes"][str(game)]
    name = cache["caches"][str(universe_id)]["name"]

    while True:
        clear()
        total = 0
        playtimes = {}
        stats = json.loads(open("./server/stats.json").read())
        for user_id, statistics in stats.items():
            if str(game) in statistics["games_playtime"]:
                playtimes[str(user_id)] = statistics["games_playtime"][str(game)]["playtime"]
                total += statistics["games_playtime"][str(game)]["playtime"]

        timestamp_date = datetime.now().strftime("%m-%d-%Y")
        timestamp_time = datetime.now().strftime("%H:%M:%S")
        print(f"{gold}{bold}[Leaderboard for {name}] [Live]{end}")
        print(f"Current Date/Time: {timestamp_time} @ {timestamp_date}")
        print(f"{bold}{underline}Total Server Playtime:{end} {total / 3600:.2f}h\n")

        print(f"{bold}Playtime for Top 20 Users:{end}")
        playtimes = sorted(playtimes.items(), key=lambda item: item[1], reverse=True)[:20]
        for i, (user, playtime) in enumerate(playtimes, start=1):
            print(format_leaderboard(f"[#{i}] {user_dict[int(user)]["display_name"]} ({playtime / 3600:.2f}h)", i))
        time.sleep(5)

if os.path.exists("./server/playtime_tools.json"):
    data = json.loads(open("./server/playtime_tools.json", "r").read())
else:
    data = {
        "version": 3,
        "weeks": []
    }
    open("./server/playtime_tools.json", "w").write(json.dumps(data, indent=2))

cache = json.loads(open("./server/cached_ids.json").read())
while True:
    clear()
    print(f"{gold}{bold}[Playtime Tools] [v2.2.0]{end}")
    print("Generate playtime leaderboards for Roblox Invites easily! More features coming soon™")
    print("Supports Roblox Invites v5.0.0 - v5.1.0")
    print("Data Version: v3")

    print("\nLatest changes:")
    print("    - As of Roblox Invites v5.1.0, 'games_played' does not exist within a stats dict. This has been accounted for.")
    print("    - Added live leaderboards")

    print("\nAvailable commands:")
    print("    - /lb - Generates leaderboards for all data (''), for the current week ('weekly'), or for a range of weeks ('range')")
    print("    - /save - Saves playtime data to /server/playtime_tools.json")
    print("    - /game [GAME_NAME] - Generates leaderboards for a specific game (requires up-to-date stats.json in /server)")
    print("    - /live - Generates an up-to-date leaderboard from stats.json (requires up-to-date stats.json in /server)")
    print("    - /live_game [GAME_NAME] - Generates an up-to-date leaderboard for a game (requires up-to-date stats.json in /server)")

    print(f"\nWeeks saved: {len(data["weeks"])}")
    command = input("Enter a command: ").lower().strip()

    args = command.split(" ")[1:]
    if command.startswith("/lb"):
        if len(args) == 0:
            this_week = data["weeks"][len(data["weeks"]) - 1]
            generate_stats("all", this_week["total"], this_week["playtimes"], this_week["game_playtimes"])
            continue
        if args[0] == "weekly":
            last_week = get_diff(len(data["weeks"]) - 2, len(data["weeks"]) - 1)
            generate_stats("weekly", last_week["total"], last_week["playtimes"], last_week["game_playtimes"])
        elif args[0] == "range":
            if len(args) != 3:
                continue
            range = get_diff(int(args[1]) - 1, int(args[2]) - 1)
            generate_stats("range", range["total"], range["playtimes"], range["game_playtimes"])
    elif command.startswith("/game "):
        if len(args) == 0:
            continue
        generate_game_stats(game_select(command.split("/game ")[1]))
    elif command == "/live":
        live_stats()
    elif command.startswith("/live_game "):
        if len(args) == 0:
            continue
        live_game_stats(game_select(command.split("/live_game ")[1]))
    elif command == "/save":
        save_playtime_data()