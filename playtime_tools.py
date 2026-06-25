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

def save_playtime_data():
    data["weeks"] += [json.loads(open("./server/stats.json").read())]
    open("./server/playtime_tools.json", "w").write(json.dumps(data, indent=2))

def get_data(stats={}):
    total = 0
    playtimes = {}
    game_playtimes = {}
    if stats == {}:
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

def get_diff(week_1, week_2):
    diff = {}
    new = data["weeks"][week_2]
    old = data["weeks"][week_1]
    for user in new.keys():
        if user not in old:
            diff[user] = new[user]
            continue
        diff[user] = {"games_playtime": {}}
        diff[user]["total_playtime"] = new[user]["total_playtime"] - old[user]["total_playtime"]
        for game in new[user]["games_playtime"].keys():
            if not game in old[user]["games_playtime"]:
                diff[user]["games_playtime"][game] = new[user]["games_playtime"][game]
                continue
            diff[user]["games_playtime"][game] = {"playtime": new[user]["games_playtime"][game]["playtime"] - old[user]["games_playtime"][game]["playtime"]}
    return diff

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

def user_select(query):
    users = json.loads(open("./server/users.json").read())
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
    stats = data["weeks"][len(data["weeks"]) - 1]
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

def generate_user_stats(user):
    global cache

    return user # wip, gotta rewrite the backend first

def live_stats():
    while True:
        cache = json.loads(open("./server/cached_ids.json").read())
        total, playtimes, game_playtimes = get_data()
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
        cache = json.loads(open("./server/cached_ids.json").read())
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
        "version": 4,
        "weeks": []
    }
    open("./server/playtime_tools.json", "w").write(json.dumps(data, indent=2))

cache = json.loads(open("./server/cached_ids.json").read())
while True:
    clear()
    print(f"{gold}{bold}[Playtime Tools] [v3.0.0]{end}")
    print("Generate playtime leaderboards for Roblox Invites easily! More features coming soon™")
    print("Supports Roblox Invites v5.0.0 - v5.1.0")
    print("Data Version: v4")

    print("\nLatest changes:")
    print("    - Data is now dynamically derived from user stats instead of being stored explictly.")

    print("\nAvailable commands:")
    print("    - /lb - Generates leaderboards for all data (''), for the current week ('weekly'), or for a range of weeks ('range')")
    print("    - /save - Saves playtime data and statistics to /server/playtime_tools.json")
    print("    - /game [GAME_NAME] - Generates leaderboards for a specific game (requires at least 1+ week saved)")
    print("    - /live - Generates an up-to-date leaderboard from stats.json (requires up-to-date stats.json in /server)")
    print("    - /live_game [GAME_NAME] - Generates an up-to-date leaderboard for a game (requires up-to-date stats.json in /server)")
    print("    - (WIP) /user [USERNAME] - Generates a profile card for a given username")

    print(f"\nWeeks saved: {len(data["weeks"])}")
    command = input("Enter a command: ").lower().strip()

    args = command.split(" ")[1:]
    if command.startswith("/lb"):
        if len(args) == 0:
            generate_stats("all", *get_data(data["weeks"][len(data["weeks"]) - 1]))
            continue
        if args[0] == "weekly":
            last_week = get_diff(len(data["weeks"]) - 2, len(data["weeks"]) - 1)
            generate_stats("weekly", *get_data(last_week))
        elif args[0] == "range":
            if len(args) != 3:
                continue
            range = get_diff(int(args[1]) - 1, int(args[2]) - 1)
            generate_stats("range", *get_data(range))
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
    elif command == "/user":
        if len(args) != 1:
            continue
        generate_user_stats(user_select(args[0]))