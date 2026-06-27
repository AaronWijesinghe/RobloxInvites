import os
import json
import time
import requests
from datetime import datetime

gold = "\033[0;33m"
silver = "\033[38;5;250m"
bronze = "\033[38;5;173m"
bold = "\033[1m"
underline = "\033[4m"
end = "\033[0m"

# this should chdir to the Roblox Invites root directory.
# ideally, you're running the source code within the Roblox Invites root directory,
# but if you compile this into an app this should still work
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

def get_number(string):
    new_string = ""
    scanning_place_id = False
    for char in string:
        if char.isdigit() and not scanning_place_id:
            scanning_place_id = True
            new_string += char
        elif char.isdigit() and scanning_place_id:
            new_string += char
        elif not char.isdigit() and scanning_place_id:
            break
    return new_string

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
    open("./server/invites_tools.json", "w").write(json.dumps(data, indent=2))

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
    for game in games:
        if query.lower() in game.lower():
            return game

def user_select(query):
    users = json.loads(open("./server/users.json").read())
    for user in users:
        if query.lower() in user["username"].lower():
            return (user["user_id"], user["username"], user["display_name"])

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

def generate_user_stats(user_id, user_name, display_name):
    global cache

    clear()
    if user_id == None:
        print(f"{gold}{bold}[Error]{end}")
        input("This user couldn't be found.")
        return

    creation_date = datetime.now().strftime("%m-%d-%Y")
    creation_time = datetime.now().strftime("%H:%M:%S")

    total, playtimes, game_playtimes = get_data({"user_id": data["weeks"][len(data["weeks"]) - 1][str(user_id)]})
    total_server, playtimes_server, game_playtimes_server = get_data(data["weeks"][len(data["weeks"]) - 1])
    playtimes_server = sorted(playtimes_server.items(), key=lambda item: item[1], reverse=True)
    game_playtimes_server = sorted(game_playtimes_server.items(), key=lambda item: item[1], reverse=True)
    
    total_weekly, playtimes_weekly, game_playtimes_weekly = get_data({"user_id": get_diff(len(data["weeks"]) - 2, len(data["weeks"]) - 1)[str(user_id)]})
    total_server_weekly, playtimes_server_weekly, game_playtimes_server_weekly = get_data(get_diff(len(data["weeks"]) - 2, len(data["weeks"]) - 1))
    playtimes_server_weekly = sorted(playtimes_server_weekly.items(), key=lambda item: item[1], reverse=True)
    game_playtimes_server_weekly = sorted(game_playtimes_server_weekly.items(), key=lambda item: item[1], reverse=True)

    print(f"{gold}{bold}[{display_name}'s usercard]{end}")
    print(f"Created on {creation_date} @ {creation_time} EST\n")

    print(f"{bold}Your Playtimes:{end}")
    print(f"Overall Playtime:{end} {total / 3600:.2f}h")
    print(f"Weekly Playtime:{end} {total_weekly / 3600:.2f}h\n")
    
    print(f"{bold}Your Standings:{end}")
    print(f"Overall Leaderboard Position:{end} #{playtimes_server.index((str(user_id), total)) + 1}")
    print(f"Weekly Leaderboard Position:{end} #{playtimes_server_weekly.index((str(user_id), total_weekly)) + 1}\n")

    print(f"{bold}Your Top 5 Games Overall:{end}")
    game_playtimes = sorted(game_playtimes.items(), key=lambda item: item[1], reverse=True)[:5]
    for i, (game, playtime) in enumerate(game_playtimes, start=1):
        universe_id = cache["indexes"][str(game)]
        name = cache["caches"][str(universe_id)]["name"]
        print(format_leaderboard(f"[#{i}] {name}: {playtime / 3600:.2f}h", i))

    print(f"\n{bold}Your Top 5 Games This Week:{end}")
    game_playtimes_weekly = sorted(game_playtimes_weekly.items(), key=lambda item: item[1], reverse=True)[:5]
    for i, (game, playtime) in enumerate(game_playtimes_weekly, start=1):
        universe_id = cache["indexes"][str(game)]
        name = cache["caches"][str(universe_id)]["name"]
        print(format_leaderboard(f"[#{i}] {name}: {playtime / 3600:.2f}h", i))
    input("\nPress ENTER to return to the main menu. ")

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

def add_custom_title():
    while True:
        clear()
        print(f"{gold}[Add Custom Title]{end}")
        place_id = get_number(input("Enter the place ID or the link of a Roblox game: "))
        message = input("Enter the custom title ({0} represents the display name of a user): ")
        hex_color = input("Enter the hex code of the color: ").lower()
        name = input("Enter game name: ")
        universe_id = requests.get(
            f"https://apis.roblox.com/universes/v1/places/{place_id}/universe"
        ).json()["universeId"]

        ct_path = "./server/custom_titles.json"
        ct = json.loads(open(ct_path).read())
        ct["titles"][str(universe_id)] = {
            "title": message,
            "color": hex_color,
            "game": name,
            "place_id": place_id,
        }
        open(ct_path, "w").write(json.dumps(ct, indent=4))

        if input("\nDone! Add another custom title (y/N)? ") != "y":
            break

def add_user(username=None):
    clear()
    print(f"{gold}[Add User]{end}")
    if username is None:
        username = input("Enter the username of the player you want to add: ")
        print("")

    print(f"You are trying to add @{username} to your Roblox Invites instance.")
    if input("Type 'y' to confirm this. ") != "y":
        return

    users_path = "./server/users.json"
    users = json.loads(open(users_path).read())
    users += [{
        "username": username
    }]
    open(users_path, "w").write(json.dumps(users, indent=4))

    input("\nDone! Press ENTER to return to the main menu. ")

if os.path.exists("./server/invites_tools.json"):
    data = json.loads(open("./server/invites_tools.json", "r").read())
else:
    data = {
        "version": 4,
        "weeks": []
    }
    open("./server/invites_tools.json", "w").write(json.dumps(data, indent=2))

version = "4.0.0"
cache = json.loads(open("./server/cached_ids.json").read())
while True:
    clear()
    print(f"{gold}{bold}[Invites Tools] [v{version}]{end}")
    print("A set of useful tools for Roblox Invites!")
    print("Supports Roblox Invites v5.0.0 - v5.3.0")
    print("Data Version: v4")

    print("\nLatest changes:")
    print("    - Merged the Custom Title Wizard into Invites Tools!")
    print("    - Renamed playtime_tools.json to invites_tools.json")

    print("\nAvailable commands:")
    print("    - /lb ['' | 'weekly | 'range']- Generates leaderboards for all data, for the current week, or for a range of weeks")
    print("    - /save - Saves playtime data and statistics to /server/invites_tools.json")
    print("    - /game [GAME_NAME] - Generates leaderboards for a specific game (requires at least 1+ week saved)")
    print("    - /live - Generates up-to-date leaderboards from stats.json (requires up-to-date stats.json in /server)")
    print("    - /live_game [GAME_NAME] - Generates up-to-date leaderboards for a game (requires up-to-date stats.json in /server)")
    print("    - /user [USERNAME] - Generates a profile card for a given username")
    print("    - /add_ct - Opens a wizard that lets you add custom titles")
    print("    - /add_user ['' | USER]- Adds a new user to your Roblox Invites instance")

    print(f"\nWeeks saved: {len(data["weeks"])}")
    print(f"Roblox Invites Server Root Path: {os.getcwd()}")
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
    elif command.startswith("/user "):
        if len(args) != 1:
            continue
        generate_user_stats(*user_select(args[0]))
    elif command == "/user_all":
        users = json.loads(open("./server/users.json").read())
        for user in users:
            generate_user_stats(user["user_id"], user["username"], user["display_name"])
    elif command == "/add_ct":
        add_custom_title()
    elif command.startswith("/add_user"):
        if len(args) == 0:
            add_user()
        else:
            add_user(args[0])