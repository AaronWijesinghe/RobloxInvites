import os
import json
import time
import requests
import pyperclip
from sys import exit
from datetime import datetime

gold = "\033[0;33m"
silver = "\033[38;5;250m"
bronze = "\033[38;5;173m"
bold = "\033[1m"
underline = "\033[4m"
end = "\033[0m"

red = 12127505
orange = 16742912
yellow = 13220620
green = 2206732
blue = 3447003
purple = 7419530
gray = 7303282

# this should chdir to the Roblox Invites root directory.
# ideally, you're running the source code within the Roblox Invites root directory,
# but if you compile this into an app this should still work
os.chdir(os.path.dirname(__file__))
#os.chdir("/Users/aaron/Desktop/Projects/RobloxInvites")
users = json.loads(open("./server/users.json").read())

def send_embed(title, desc, color, webhook):
    data = {
        "embeds": [{"title": title, "description": desc, "color": color}],
        "components": [],
    }
    requests.post(webhook, json=data)

def build_user_dict():
    global user_dict
    user_dict = {}
    for user in users:
        try:
            user_dict[user["user_id"]] = {
                "username": user["username"],
                "display_name": user["display_name"]
            }
        except:
            pass
build_user_dict()

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
    stats = json.loads(open("./server/stats.json").read())
    for user in stats:
        if stats[user]["currently_playing"] != {}:
            currently_playing = stats[user]["currently_playing"]
            stats[user]["games_playtime"][str(currently_playing["root_place_id"])]["playtime"] += round(time.time() - currently_playing["start"])
    data["weeks"] += [stats]
    open("./server/invites_tools.json", "w").write(json.dumps(data, indent=2))

def get_data(stats={}):
    total = 0
    playtimes = {}
    game_playtimes = {}
    if stats == {}:
        stats = json.loads(open("./server/stats.json").read())
    for user in stats:
        if stats[user]["currently_playing"] != {}:
            currently_playing = stats[user]["currently_playing"]
            if str(currently_playing["root_place_id"]) in stats[user]["games_playtime"]:
                stats[user]["games_playtime"][str(currently_playing["root_place_id"])]["playtime"] += round(time.time() - currently_playing["start"])
            else:
                stats[user]["games_playtime"][str(currently_playing["root_place_id"])] = {"playtime": round(time.time() - currently_playing["start"])}
            stats[user]["currently_playing"] = {}

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
        diff[user] = {"games_playtime": {}, "currently_playing": {}}
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

    games = list(game_cache.items())
    for (game, id) in games:
        if query.lower() in game.lower():
            return id

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
    build_user_dict()
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
    build_user_dict()
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

    total, playtimes, game_playtimes = get_data({str(user_id): data["weeks"][len(data["weeks"]) - 1][str(user_id)]})
    total_server, playtimes_server, game_playtimes_server = get_data(data["weeks"][len(data["weeks"]) - 1])
    playtimes_server = sorted(playtimes_server.items(), key=lambda item: item[1], reverse=True)
    game_playtimes_server = sorted(game_playtimes_server.items(), key=lambda item: item[1], reverse=True)
    
    total_weekly, playtimes_weekly, game_playtimes_weekly = get_data({str(user_id): get_diff(len(data["weeks"]) - 2, len(data["weeks"]) - 1)[str(user_id)]})
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
        build_user_dict()
        cache = json.loads(open("./server/cached_ids.json").read())
        total, playtimes, game_playtimes = get_data()
        timestamp_date = datetime.now().strftime("%m-%d-%Y")
        timestamp_time = datetime.now().strftime("%H:%M:%S")

        clear()
        print(f"{gold}{bold}[Server Leaderboard] [Live]{end}")
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
        open(ct_path, "w").write(json.dumps(ct, indent=2))

        if input("\nDone! Add another custom title (y/N)? ") != "y":
            break

def modify_blacklist(place_id=None, mode="add"):
    clear()
    print(f"{gold}[{mode.capitalize()} User (Blacklist)]{end}")
    if place_id is None:
        place_id = input(f"Enter the place ID you want to {mode}: ")
    else:
        print(f"You are {"adding" if mode == "add" else "removing"} \"{place_id}\" {"to" if mode == "add" else "from"} the blacklist.")
    place_id = int(place_id)

    blacklist_path = "./server/blacklisted.json"
    if os.path.exists(blacklist_path):
        blacklist = json.loads(open(blacklist_path).read())
    else:
        blacklist = []
    if mode == "add":
        game = input(f"Enter the name of the game you want to {mode}: ")
        blacklist += [{
            "place_id": place_id,
            "game": game,
        }]
    elif mode == "remove":
        for i, game in enumerate(list(blacklist)):
            if game["place_id"] == place_id:
                del blacklist[i]

    open(blacklist_path, "w").write(json.dumps(blacklist, indent=2))
    input(f"{"\n" if mode == "add" else ""}Done! Press ENTER to return to the main menu. ")

def modify_users(username=None, mode="add"):
    clear()
    print(f"{gold}[{mode.capitalize()} User]{end}")
    if username is None:
        username = input(f"Enter the username of the player you want to {mode}: ")
        print("")

    print(f"You are trying to {mode} @{username} {"to" if mode == "add" else "from"} your Roblox Invites instance.")
    if input("Type 'y' to confirm this. ") != "y":
        return

    users_path = "./server/users.json"
    if os.path.exists(users_path):
        users = json.loads(open(users_path).read())
    else:
        users = []
    if mode == "add":
        req = requests.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [username]}).json()
        if len(req["data"]) == 0:
            input("\nThis user doesn't exist. ")
            return

        users += [{
            "username": req["data"][0]["name"],
            "user_id": req["data"][0]["id"],
            "display_name": req["data"][0]["displayName"]
        }]
    elif mode == "remove":
        for i, user in enumerate(list(users)):
            if user["username"].lower() == username.lower():
                del users[i]

    open(users_path, "w").write(json.dumps(users, indent=2))
    input("\nDone! Press ENTER to return to the main menu. ")

def set_cookie():
    clear()
    print(f"{gold}[Set Cookie]{end}")
    print("Copy your .ROBLOSECURITY cookie.")
    while not pyperclip.paste().startswith("_|WARNING:-DO-NOT-SHARE-THIS.--Sharing-this-will-allow-someone-to-log-in-as-you-and-to-steal-your-ROBUX-and-items."):
        time.sleep(1)
    cookies = [pyperclip.paste()]
    pyperclip.copy("")
    open("./server/cookies.json", "w").write(json.dumps(cookies, indent=2))
    input("Set cookie! Press ENTER to return to the main menu. ")

def shutdown_server():
    clear()
    print(f"{gold}[Shutdown Server]{end}")
    print("Waiting for Roblox Invites to stop...")
    while os.path.exists("session.lock"):
        time.sleep(1)
    
    print("Roblox Invites has stopped. Calculating playtime data...")
    stats = json.loads(open("./server/stats.json").read())
    for user in stats:
        if stats[user]["currently_playing"] != {}:
            currently_playing = stats[user]["currently_playing"]
            if str(currently_playing["root_place_id"]) in stats[user]["games_playtime"]:
                stats[user]["games_playtime"][str(currently_playing["root_place_id"])]["playtime"] += round(time.time() - currently_playing["start"])
            else:
                stats[user]["games_playtime"][str(currently_playing["root_place_id"])] = {"playtime": round(time.time() - currently_playing["start"])}
        stats[user]["currently_playing"] = {}
    open("./server/stats.json", "w").write(json.dumps(stats, indent=2))
    if os.path.exists("./server/old_user_presences.json"):
        os.remove("./server/old_user_presences.json")
    
    print("\nAttempting to shut down server (requires password)...")
    os.system("sudo shutdown -h now")
    exit()

def announce():
    clear()
    print(f"{gold}[Send Announcement]{end}")
    if not os.path.exists("./server/webhooks.json"):
        input("Couldn't find webhooks.json. Make sure you're running Roblox Invites v5.4.0 or higher. ")
        return
    
    webhooks = json.loads(open("./server/webhooks_testing.json").read())
    announcement_webhook = webhooks["announcement_webhook"]

    title = input("Enter announcement title: ")
    message = ""
    print("Enter announcement message (type EXIT [case-sensitive] when finished, ENTER for newline):")
    while True:
        new = input("> ")
        if new == "EXIT":
            break
        message += new+"\n"
    message = message[:-1]
    send_embed(title, message, blue, announcement_webhook)
            
version = "4.4.0"
data_version = 4
cache = json.loads(open("./server/cached_ids.json").read())
if os.path.exists("./server/invites_tools.json"):
    data = json.loads(open("./server/invites_tools.json", "r").read())
else:
    data = {
        "version": data_version,
        "weeks": []
    }
    open("./server/invites_tools.json", "w").write(json.dumps(data, indent=2))
while True:
    clear()
    print(f"{gold}{bold}[Invites Tools] [v{version}]{end}")
    print("A set of useful tools for Roblox Invites!")
    print("Supports Roblox Invites v5.0.0 - v5.4.0")
    print(f"Data Version: v{data_version}")

    print(f"\n{bold}Latest changes:{end}")
    print("    - Added clean exit on CTRL+C")

    print(f"\n{bold}Leaderboard commands:{end}")
    print("    - /save - Saves a period of player statistics to /server/invites_tools.json")
    print("    - /lb ['' | 'weekly | 'range'] - Generates leaderboards for all data, for the current week, or for a range of weeks (requires at least 1+ week saved)")
    print("    - /game [GAME_NAME] - Generates leaderboards for a specific game (requires at least 1+ week saved)")
    print("    - /live - Generates up-to-date leaderboards from stats.json (requires up-to-date stats.json in /server)")
    print("    - /live_game [GAME_NAME] - Generates up-to-date leaderboards for a game (requires up-to-date stats.json in /server)")
    print("    - /user [USERNAME] - Generates a profile card for a given username")

    print(f"\n{bold}Server commands:{end}")
    print("    - /add_ct - Opens a wizard that lets you add custom titles")
    print("    - /add_user ['' | USER] - Adds a new user to your Roblox Invites instance")
    print("    - /remove_user ['' | USER] - Removes a user from your Roblox Invites instance")
    print("    - /add_blacklist - Adds a game ID to the blacklist")
    print("    - /remove_blacklist - Removes a game ID from the blacklist")
    print("    - /cookie - Sets the .ROBLOSECURITY cookie in ./server/cookies.json")

    print(f"\n{bold}Other commands:{end}")
    print("    - /shutdown - Waits for Roblox Invites to stop, calculates running playtimes, and shuts down the server")
    print("    - /announce - Opens a wizard that sends announcements to your Announcements webhook (requires Roblox Invites v5.4.0+)")

    print(f"\nWeeks saved: {len(data["weeks"])}")
    print(f"Roblox Invites Server Root Path: {os.getcwd()}")

    try:
        command = input("Enter a command: ").lower().strip()
    except:
        exit()

    try:
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
                modify_users(None, "add")
            else:
                modify_users(args[0], "add")
        elif command.startswith("/remove_user"):
            if len(args) == 0:
                modify_users(None, "remove")
            else:
                modify_users(args[0], "remove")
        elif command == "/shutdown":
            shutdown_server()
        elif command.startswith("/add_blacklist"):
            if len(args) == 0:
                modify_blacklist(None, "add")
            else:
                modify_blacklist(args[0], "add")
        elif command.startswith("/remove_blacklist"):
            if len(args) == 0:
                modify_blacklist(None, "remove")
            else:
                modify_blacklist(args[0], "remove")
        elif command == "/cookie":
            set_cookie()
        elif command.startswith("/announce"):
            announce()
    except:
        pass