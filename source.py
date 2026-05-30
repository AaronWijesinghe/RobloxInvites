import atexit
import getpass
import json
import os
import shutil
import sys
import time
from datetime import datetime
from io import BytesIO
from itertools import batched
from sys import exit
from copy import deepcopy

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

os.chdir(os.path.dirname(__file__))
if os.path.exists("session.lock"):
    print("Another instance of Roblox Invites is already running.")
    exit()
else:
    open("session.lock", "w").write("Session Locked")


def cleanup():
    if os.path.exists("session.lock"):
        os.remove("session.lock")


atexit.register(cleanup)

errors = {
    "requests.exceptions.ConnectionError": "[ConnectionError] Couldn't connect to the Roblox servers.",
    "requests.exceptions.ConnectTimeout": "[ConnectTimeout] Your request with the Roblox servers timed out.",
    "requests.exceptions.SSLError": "[SSLError] Couldn't connect to the Roblox servers. Your internet may be blocking Roblox.",
    "requests.exceptions.ReadTimeout": "[ReadTimeout] Your request with the Roblox servers timed out.",
}

gold = "\033[0;33m"
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


def clear():
    print("\033[2J\033[3J\033[H", end="")


def send_embed(title, desc, color, webhook, join_embed_data=None):
    data = {
        "embeds": [{"title": title, "description": desc, "color": color}],
        "components": [],
    }
    if join_embed_data is not None:
        data["embeds"] += [{"title": join_embed_data[0], "url": join_embed_data[1]}]
    session.post(webhook, json=data)


def send_file(webhook, file_to_share):
    file_buffer = BytesIO(open(file_to_share, "rb").read())
    files = {"file": (os.path.basename(file_to_share), file_buffer)}
    session.post(webhook, files=files)


def write_to_log(type, message):
    os.makedirs("./logs/", exist_ok=True)
    timestamp_date = datetime.now().strftime("%m-%d-%Y")
    timestamp_time = datetime.now().strftime("%H:%M:%S")
    open(f"./logs/{timestamp_date}.log", "a").write(f"[{timestamp_time}] [{type.upper()}] {message}\n")


def load_data(
    file: str,
    no_exist_data: dict | list | None = {},
    no_exist_ok: bool = True,
    no_exist_message: str = "",
) -> dict | list:
    if os.path.exists(f"./server/{file}"):
        return json.loads(open(f"./server/{file}").read())
    elif no_exist_ok:
        write_to_log("info", f"Created file './server/{file}' with data '{no_exist_data}'")
        save_data(no_exist_data, file)
        return {}
    elif not no_exist_ok and no_exist_message != "":
        write_to_log("fatal", no_exist_message)
        save_data(no_exist_data, file)
        print(f"{underline}{no_exist_message}{end}")
        exit()
    return {}


def save_data(data, file):
    open(f"./server/{file}", "w").write(json.dumps(data, indent=2))


def check_joins(i, place_id, game_instance_id):
    global user_presences

    joined = []
    for _ in range(len(list(user_presences.keys()))):
        if (
            user_presences[str(user_ids[_])]["place_id"] == place_id
            and user_presences[str(user_ids[_])]["game_instance_id"] == game_instance_id
            and _ != i
        ):
            joined += [(displaynames[_], usernames[_])]
    return joined


def cache_id(int_place_id: int) -> None:
    for key in ["indexes", "caches"]:
        if key not in cached_ids:
            cached_ids[key] = {}

    place_id = str(int_place_id)
    if place_id not in cached_ids["indexes"]:
        universe_id = session.get(f"https://apis.roblox.com/universes/v1/places/{place_id}/universe").json()["universeId"]
        game_data = session.get(f"https://games.roblox.com/v1/games?universeIds={universe_id}").json()
        game_name = game_data["data"][0]["name"]
        game_root_place_id = game_data["data"][0]["rootPlaceId"]
        cached_ids["indexes"][place_id] = universe_id
        cached_ids["caches"][str(universe_id)] = {
            "root_place_id": game_root_place_id,
            "name": game_name,
        }
        save_data(cached_ids, "cached_ids.json")


def get_universe_id(place_id):
    try:
        cache_id(place_id)
        if str(place_id) in cached_ids["indexes"]:
            return cached_ids["indexes"][str(place_id)]
    except:
        return None


def get_root_place_id(place_id):
    try:
        cache_id(place_id)
        if str(place_id) in cached_ids["indexes"]:
            universe_id = cached_ids["indexes"][str(place_id)]
            if "root_place_id" in cached_ids["caches"][str(universe_id)]:
                return cached_ids["caches"][str(universe_id)]["root_place_id"]
    except:
        return None


def check_root_place_id(place_id_1, place_id_2):
    if get_root_place_id(place_id_1) == get_root_place_id(place_id_2):
        return True
    else:
        return False


def get_game_data(universe_id, key):
    try:
        game_data = session.get(f"https://games.roblox.com/v1/games?universeIds={universe_id}").json()["data"][0][key]
        if type(game_data) is str:
            return game_data.strip()
        else:
            return game_data
    except:
        return None


def get_server_data(place_id, key):
    try:
        server_data = session.get(f"https://games.roblox.com/v1/games/{place_id}/servers/0?sortOrder=2&excludeFullGames=false&limit=10").json()["data"][0][key]
        return server_data
    except:
        return None


def game_ends_in_punctuation(game_name):
    try:
        last_letter = game_name[-1]
        if last_letter in [".", "?", "!", ";", ":"]:
            return True
        else:
            return False
    except:
        return False


def send_invite(i, place_id, game_instance_id, transfer=False):
    global usernames
    global displaynames
    global blacklisted_ids
    global custom_titles

    if str(user_ids[i]) in transfers:
        del transfers[str(user_ids[i])]

    if place_id in blacklisted_ids:
        return

    try:
        universe_id = get_universe_id(place_id)
        game = get_game_data(universe_id, "name")
        max_players = get_server_data(place_id, "maxPlayers")
    except:
        return
    playtime_str = get_playtime_str(i, place_id, "both")

    exclamation = "" if game_ends_in_punctuation(game) else "!"
    period = "" if game_ends_in_punctuation(game) else "."

    game_url = f"roblox://experiences/start?placeId={place_id}&gameInstanceId={game_instance_id}"
    embed_title = f"{displaynames[i]} has joined a game!"
    embed_desc = f"**Join {displaynames[i]} (@{usernames[i]}) in** *{game}*{exclamation}\nTotal playtime for this game: {playtime_str}\n\nOpen the link below, or copy this URL:\n-# {game_url}"
    embed_color = green

    use_join_embed = True
    join_embed_title = f"Join {displaynames[i]}"
    join_embed_url = f"https://join.rblxevnts.co/?placeId={place_id}&gameInstanceId={game_instance_id}"

    if str(universe_id) in custom_titles:
        embed_title = custom_titles[str(universe_id)]["title"].format(displaynames[i])
        embed_color = int(custom_titles[str(universe_id)]["color"], 16)

    if transfer:
        if str(universe_id) in custom_titles:
            embed_title = f"{custom_titles[str(universe_id)]["title"].format(displaynames[i])[:-1]} in a new server!"
        else:
            embed_title = f"{displaynames[i]} transferred servers!"
        embed_desc = f"{displaynames[i]} (@{usernames[i]}) has transferred to a different server in *{game}*{period}\nTotal playtime for this game: {playtime_str}\n\nOpen the link below, or copy this URL:\n-# {game_url}"

    if max_players == 1:
        embed_desc = f"{displaynames[i]} (@{usernames[i]}) is playing *{game}*{exclamation}\nHowever, you can't join them because the max server size is 1 player.\nTotal playtime for this game: {playtime_str}\n\n-# {game_url}"
        if str(universe_id) not in custom_titles:
            embed_color = orange
        use_join_embed = False

    joined = check_joins(i, place_id, game_instance_id)
    if len(joined) > 0:
        if embed_title == f"{displaynames[i]} has joined a game!":
            embed_title = f"{displaynames[i]} has joined {len(joined)} user(s)!"
        else:
            embed_title += f" (+{len(joined)})"

        embed_desc = f"**{displaynames[i]} (@{usernames[i]}) just joined:**"
        for user in joined:
            embed_desc += f"\n- {user[0]} (@{user[1]})"
        embed_desc += f"\n\nTotal playtime for this game: {playtime_str}\n**Join them** in *{game}* by opening the link below or by copying the URL!\n-# {game_url}"
        join_embed_title += f" and {len(joined)} other(s)"

    send_embed(
        embed_title,
        embed_desc,
        embed_color,
        webhook,
        (join_embed_title, join_embed_url) if use_join_embed else None,
    )


def send_leave_message(i, place_id, type):
    global webhook

    playtime_str = get_playtime_str(i, place_id, "current")
    playtime_str_2 = get_playtime_str(i, place_id, "both")
    universe_id = get_universe_id(place_id)
    game = get_game_data(universe_id, "name")
    period = "" if game_ends_in_punctuation(game) else "."

    if game is None:
        return

    embed_title = f"{displaynames[i]} left *{game}*{period}"
    embed_desc = f"Time played: {playtime_str}\nTotal playtime for this game: {playtime_str_2}"

    if type == "website":
        embed_desc = f"{displaynames[i]} (@{usernames[i]}) is currently on the Roblox website or transferring between servers.\nIt's also possible that Roblox's APIs are showing this message in error.\n\nTime played: {playtime_str}\nTotal playtime for this game: {playtime_str_2}"

    if str(universe_id) in custom_titles:
        embed_title = (
            custom_titles[str(universe_id)]["title"]
            .format(displaynames[i])
            .replace(f"{displaynames[i]} is", f"{displaynames[i]} was")
            .replace("!", ".")
        )
        if type == "website":
            embed_desc = embed_desc.replace("is currently", f"has left *{game}*{period} They are")
        else:
            embed_desc = f"{displaynames[i]} (@{usernames[i]}) has left *{game}*{period}\n" + embed_desc

    send_embed(embed_title, embed_desc, red, webhook)


def fix_stats(user_id):
    default_stats = {
        "total_playtime": 0,
        "games_played": [],
        "games_playtime": {},
        "currently_playing": {},
    }
    if str(user_id) not in stats:
        stats[str(user_id)] = {}
    for key in default_stats.keys():
        if key not in stats[str(user_id)]:
            stats[str(user_id)][key] = default_stats[key]
    save_data(stats, "stats.json")


def get_playtime_str(i, place_id, playtime_type):
    user_id = str(user_ids[i])

    playtime = 0
    rpid = get_root_place_id(place_id)
    fix_stats(user_id)

    if playtime_type == "both" and str(rpid) in stats[user_id]["games_playtime"]:
        playtime += stats[user_id]["games_playtime"][str(rpid)]["playtime"]
    if (
        playtime_type in ["current", "both"]
        and "root_place_id" in stats[user_id]["currently_playing"]
    ):
        if stats[user_id]["currently_playing"]["root_place_id"] == rpid:
            playtime += (round(time.time()) - stats[user_id]["currently_playing"]["start"])

    hours = round(playtime // 3600)
    minutes = round((playtime % 3600) // 60)
    seconds = playtime % 60
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


def start_tracking_playtime(int_user_id, place_id, game_instance_id):
    user_id = str(int_user_id)
    fix_stats(user_id)
    if stats[user_id]["currently_playing"] != {}:
        finish_tracking_playtime(user_id)
    root_place_id = get_root_place_id(place_id)
    if root_place_id not in stats[user_id]["games_played"]:
        stats[user_id]["games_played"] += [root_place_id]
    stats[user_id]["currently_playing"] = {
        "root_place_id": root_place_id,
        "game_instance_id": game_instance_id,
        "start": round(time.time()),
    }
    save_data(stats, "stats.json")


def finish_tracking_playtime(int_user_id):
    user_id = str(int_user_id)
    fix_stats(user_id)
    current = stats[user_id]["currently_playing"]
    if "start" in current:
        root_place_id = current.get("root_place_id")
        diff = round(time.time()) - current["start"]
        if str(root_place_id) not in stats[user_id]["games_playtime"]:
            stats[user_id]["games_playtime"][str(root_place_id)] = {"playtime": diff}
        else:
            stats[user_id]["games_playtime"][str(root_place_id)]["playtime"] += diff
        stats[user_id]["total_playtime"] = sum(
            [
                playtime["playtime"]
                for playtime in stats[user_id]["games_playtime"].values()
            ]
        )
        stats[user_id]["currently_playing"] = {}
    save_data(stats, "stats.json")


def check_presences():
    global users
    global user_ids
    global user_presences
    global checks_since_start
    global blacklisted_ids
    global blacklisted_games
    global transfers

    clear()
    print(f"{gold}[Times Checked: {checks_since_start}]{end}")
    for i, int_user_id in enumerate(user_ids):
        user_id = str(int_user_id)

        status = user_presences[user_id]["status"]
        place_id = user_presences[user_id]["place_id"]
        game_instance_id = user_presences[user_id]["game_instance_id"]

        if status in [0, 1]:
            if user_id in old_user_presences.keys():
                if old_user_presences[user_id]["status"] == 2 and user_id not in transfers:
                    transfers[user_id] = {
                        "start": time.time(),
                        "old_place_id": old_user_presences[user_id]["place_id"],
                        "old_game_instance_id": old_user_presences[user_id][
                            "game_instance_id"
                        ],
                        "username": usernames[i],
                    }
                elif user_id in transfers:
                    if time.time() - transfers[user_id]["start"] > 5:
                        send_leave_message(i, transfers[user_id]["old_place_id"], "absolute" if status == 0 else "website")
                        finish_tracking_playtime(user_id)
                        del transfers[user_id]
                elif user_id in stats:
                    if stats[user_id]["currently_playing"] != {}:
                        finish_tracking_playtime(user_id)
            print(f"{usernames[i]} is {'offline.' if status == 0 else 'on the Roblox website!'}")
        elif status == 2 and (game_instance_id is None or place_id is None):
            print(f"{usernames[i]} has their joins off, or you aren't following them.")
            print(f"   -> Follow them @ https://roblox.com/users/{user_ids[i]}/profile")
        elif status == 2:
            if user_id in old_user_presences:
                if user_id in transfers:
                    if [
                        transfers[user_id]["old_place_id"],
                        transfers[user_id]["old_game_instance_id"],
                    ] == [place_id, game_instance_id]:
                        del transfers[user_id]
                    elif check_root_place_id(transfers[user_id]["old_place_id"], place_id):
                        stats[user_id]["currently_playing"]["game_instance_id"] = game_instance_id
                        send_invite(i, place_id, game_instance_id, transfer=True)
                    else:
                        start_tracking_playtime(user_id, place_id, game_instance_id)
                        send_invite(i, place_id, game_instance_id)
                    continue

                if user_presences[user_id] != old_user_presences[user_id]:
                    if check_root_place_id(old_user_presences[user_id]["place_id"], place_id):
                        stats[user_id]["currently_playing"]["game_instance_id"] = (game_instance_id)
                        send_invite(i, place_id, game_instance_id, transfer=True)
                    else:
                        start_tracking_playtime(user_id, place_id, game_instance_id)
                        send_invite(i, place_id, game_instance_id)
            else:
                start_tracking_playtime(user_id, place_id, game_instance_id)
                send_invite(i, place_id, game_instance_id)
            print(f"{usernames[i]} is in a game: {underline}roblox://experiences/start?placeId={place_id}&gameInstanceId={game_instance_id}{end}")
        elif status == 3:
            print(f"{usernames[i]} is in Roblox Studio.")

    print(f"\n{gold}[Blacklisted Place IDs]{end}")
    for id in range(len(blacklisted_ids)):
        print(f"    - {blacklisted_ids[id]} ({blacklisted_games[id]})")
    if len(blacklisted_ids) == 0:
        print("No Place IDs are currently blacklisted.")


def get_user_ids():
    global users
    global user_ids

    new_user_indexes = []
    new_usernames = []
    for i, username in enumerate(users):
        if not ("user_id" in username and "display_name" in username):
            new_user_indexes += [i]
            new_usernames += [username["username"]]

    if len(user_ids) != len(users) and len(new_usernames) == 0:
        user_ids = [user["user_id"] for user in users]
        return
    elif len(new_usernames) == 0:
        return

    try:
        data = {"usernames": new_usernames}
        req = session.post("https://users.roblox.com/v1/usernames/users", json=data).json()
        ids = [user["id"] for user in req["data"]]
        unames = [user["name"].lower() for user in req["data"]]
        displaynames = [user["displayName"] for user in req["data"]]

        if len(unames) != len(set(unames)):
            write_to_log("fatal", "Invites can't be checked twice for the same user.")
            print(f"{underline}Invites can't be checked twice for the same user.{end}")
            exit()

        faulty_users = [user for user in new_usernames if user.lower() not in unames]
        if len(faulty_users) > 0:
            write_to_log("fatal", f"These users don't exist: [@{', @'.join(faulty_users)}]")
            print(f"{underline}These users don't exist: [@{', @'.join(faulty_users)}]{end}")
            exit()

        user_id_map = dict(zip(unames, ids))
        displayname_id_map = dict(zip(unames, displaynames))
        new_user_ids = [user_id_map[user.lower()] for user in new_usernames]
        new_display_names = [displayname_id_map[user.lower()] for user in new_usernames]
        for i_index_list, i_user_list in enumerate(new_user_indexes):
            users[i_user_list]["user_id"] = new_user_ids[i_index_list]
            users[i_user_list]["display_name"] = new_display_names[i_index_list]

        write_to_log("info", f"Added new usernames: {new_usernames}")
        save_data(users, "users.json")
        user_ids = [user["user_id"] for user in users]
    except Exception as e:
        err = f"{type(e).__module__}.{type(e).__name__}"
        if err in errors.keys():
            print(f"{underline}{errors[err]}{end}")
            exit()
        else:
            write_to_log("error", f"{err}: {str(e)}")
            print(f"{underline}An error has occured: {err}{end}")
            time.sleep(1)


def announce(operating_mode, webhook):
    match operating_mode:
        case "prod":
            write_to_log("info", f"Sent update changelog embed to {webhook}")
            send_embed("Updates", update_desc, blue, webhook)
        case "maintenance":
            write_to_log("info", f"Sent maintenance embed to {webhook}")
            send_embed(
                "Maintenance",
                f"The Roblox Invites server will be undergoing maintenance.\n\n**Reason:** {maintenance_info['reason']}\n**Timeframe:** {maintenance_info['timeframe']}",
                gray,
                webhook,
            )
            exit()
        case "incoming_upd":
            write_to_log("info", f"Sent update notice embed to {webhook}")
            send_embed(
                "Update Notice",
                f"An update is coming soon™ to a production server near you!\n\n**Version:** v{incoming_upd_info['previous_version']} -> v{version}\n**Estimated Release Time:** {incoming_upd_info['estimated_release_timeframe']}",
                yellow,
                webhook,
            )
            exit()


def check_ri_update():
    global version

    if os.path.exists(f"/Users/{getpass.getuser()}/Downloads/RobloxInvites.py"):
        write_to_log("info", "Found update!")
        write_to_log("info", "Starting backup of old server data...")
        os.makedirs("../RobloxInvitesBackups/", exist_ok=True)
        if os.path.exists(f"../RobloxInvitesBackups/{version}/"):
            shutil.rmtree(f"../RobloxInvitesBackups/{version}/")
        try:
            shutil.copytree(os.path.dirname(__file__), f"../RobloxInvitesBackups/{version}/")
        except:
            pass
        write_to_log("info", "Server backup successful!")

        write_to_log("info", "Updating Roblox Invites...")
        if os.path.exists(__file__):
            os.remove(__file__)
        if os.path.exists("session.lock"):
            os.remove("session.lock")
        os.rename(f"/Users/{getpass.getuser()}/Downloads/RobloxInvites.py", __file__)
        os.execv(sys.executable, [sys.executable] + sys.argv)


def check_ct_update():
    global version
    global custom_titles

    if os.path.exists(f"/Users/{getpass.getuser()}/Downloads/custom_titles.json"):
        write_to_log("info", "Found custom title update! Updating custom titles...")
        os.rename(
            f"/Users/{getpass.getuser()}/Downloads/custom_titles.json",
            "./server/custom_titles.json",
        )

        custom_titles_old = custom_titles
        ct_json = load_data("custom_titles.json", {"version": 0, "titles": {}})
        custom_titles = ct_json["titles"]
        custom_titles_version = ct_json["version"]
        custom_titles_delta = {"version": custom_titles_version, "titles": {}}

        ct_update_msg = ""
        added_games = {}
        updated_games = {}
        for key, value in custom_titles.items():
            if key not in custom_titles_old:
                custom_titles_delta["titles"][key] = value
                added_games[key] = value
            elif value != custom_titles_old[key]:
                custom_titles_delta["titles"][key] = value
                updated_games[key] = value

        ct_update_msg += "**Added these games:**\n"
        if added_games != {}:
            for i, (key, value) in enumerate(added_games.items()):
                if i < 20:
                    ct_update_msg += f" - {value['game']}\n    - Title: {value['title']}\n  - Color: #{value['color']}\n"
                else:
                    ct_update_msg += f"-# {len(list(added_games.keys())) - 10} more games were added.\n"
                    break
        else:
            ct_update_msg += "No new games were added.\n"

        ct_update_msg += "\n**Updated these games:**\n"
        if updated_games != {}:
            for i, (key, value) in enumerate(updated_games.items()):
                if i < 10:
                    ct_update_msg += f" - {value['game']}\n    - Title: {custom_titles_old[key]['title']} -> {value['title']}\n  - Color: #{custom_titles_old[key]['color']} -> #{value['color']}\n"
                else:
                    ct_update_msg += f"-# {len(list(updated_games.keys())) - 10} more games were updated.\n"
                    break
        else:
            ct_update_msg += "No games were updated.\n"

        ct_update_msg += "\n**JSON Updates**\ncustom_titles.json contains all custom titles used by Roblox Invites.\ncustom_titles_delta.json contains all changes from the previous build."
        save_data(custom_titles_delta, "custom_titles_delta.json")

        send_embed(
            f"**Custom Titles v{custom_titles_version}**",
            ct_update_msg,
            purple,
            ct_webhook,
        )
        send_file(ct_webhook, "./server/custom_titles.json")
        send_file(ct_webhook, "./server/custom_titles_delta.json")
        os.remove("./server/custom_titles_delta.json")

# START migration code
stats = json.loads(open("./server/stats.json", "r").read())
users = json.loads(open("./server/users.json", "r").read())
old_user_presences = json.loads(open("./server/old_user_presences.json", "r").read())
for user in users:
    if user["username"] in stats:
        stats[str(user["user_id"])] = deepcopy(stats[user["username"]])
        del stats[user["username"]]
    if user["username"] in old_user_presences:
        old_user_presences[str(user["user_id"])] = deepcopy(old_user_presences[user["username"]])
        del old_user_presences[user["username"]]
open("./server/stats.json", "w").write(json.dumps(stats, indent=2))
open("./server/old_user_presences.json", "w").write(json.dumps(old_user_presences, indent=2))

write_to_log("info", "Initalizing Roblox Invites...")
# END migration code

transfers = {}
user_presences = {}
user_ids = []
checks_since_start = 0

cookies = load_data("cookies.json", [], False, "Add a cookie to /server/cookies.json before running Roblox Invites.")
if len(cookies) > 0:
    header = {"Cookie": f".ROBLOSECURITY={cookies[0]}"}
else:
    write_to_log("fatal", "Add a cookie to /server/cookies.json before running Roblox Invites.")
    print(f"{underline}Add a cookie to /server/cookies.json before running the program.{end}")
    exit()

stats = load_data("stats.json")
cached_ids = load_data("cached_ids.json", {"indexes": [], "caches": {}})
users = load_data("users.json", [{"username": ""}], False, "At least one user must be present in /server/users.json.",)
blacklisted = load_data("blacklisted.json", [])
old_user_presences = load_data("old_user_presences.json")
custom_titles = load_data("custom_titles.json")["titles"]
user_ids = [user["user_id"] for user in users]
write_to_log("info", f"Loaded server data at {os.path.dirname(__file__)}/server/")

session = requests.Session()
session.headers.update(header)
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 503, 504],
    respect_retry_after_header=True,
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
write_to_log("info", "Initalized network session")

version = "5.0.0"
update_desc = f"""
**Roblox Invites {version}**
- Statistics and user presence data are now indexed by user ID instead of username
- Attempted to fix an issue where inactive sessions inflated total server playtime
- A given invite embed's color will only change to orange (case: max server size is 1) if there is no existing custom title for the game
    - Now, a game with a custom title but a custom color of default green will still retain the default green color in all cases

**Deprecation of --migrate**
The --migrate flag's functionality has been removed.
Instances of Roblox Invites that call "robloxinvites.py --migrate" before updating should be manually updated to prevent issues.
"""

announcement_webhook = "webhook"
webhook = "webhook"
ct_webhook = "webhook"

maintenance_info = {
    "reason": "I'll be pushing Roblox Invites version 4.2.0 to the production server.",
    "timeframe": "10-20 minutes",
}
incoming_upd_info = {
    "previous_version": "4.1.0",
    "estimated_release_timeframe": "10-20 minutes",
}
announce("prod", announcement_webhook)  # "prod" announces updates, "" announces nothing
write_to_log("info", f"Successfully initalized Roblox Invites {version}!")

while True:
    try:
        check_ri_update()
        check_ct_update()

        users = load_data("users.json", [{"username": ""}], False, "At least one user must be present in /server/users.json.")
        blacklisted = load_data("blacklisted.json", [])
        blacklisted_ids = [b["place_id"] for b in blacklisted]
        blacklisted_games = [b["game"] for b in blacklisted]
        get_user_ids()

        checks_since_start += 1
        usernames = [user["username"] for user in users]
        displaynames = [user["display_name"] for user in users]

        online_data = {"user_presences": []}
        for batched_ids in batched(user_ids, 50):
            req = session.post(
                url="https://presence.roblox.com/v1/presence/users",
                json={"userIDs": batched_ids},
                headers=header,
            )
            if req.ok:
                online_data["user_presences"] += req.json()["userPresences"]
            else:
                raise requests.exceptions.ConnectionError

        for i, user_id in enumerate(user_ids):
            user_presences[str(user_id)] = {
                "game_instance_id": online_data["user_presences"][i]["gameId"],
                "place_id": online_data["user_presences"][i]["placeId"],
                "status": online_data["user_presences"][i]["userPresenceType"],
            }

        check_presences()
        old_user_presences = deepcopy(user_presences)
        save_data(old_user_presences, "old_user_presences.json")
        time.sleep(1)
    except requests.exceptions.ConnectionError:
        clear()
        print(f"{gold}[Times Checked: {checks_since_start}]{end}")
        print(f"{errors['requests.exceptions.ConnectionError']} Retrying in 5s...")
        time.sleep(5)
    except KeyboardInterrupt:
        break
    except Exception as e:
        clear()
        err = f"{type(e).__module__}.{type(e).__name__}"
        print(f"{gold}[Times Checked: {checks_since_start}]{end}")
        print(errors[err] if err in errors.keys() else f"An error has occured: {err}")
        write_to_log("error", f"{err}: {str(e)}")
        time.sleep(1)