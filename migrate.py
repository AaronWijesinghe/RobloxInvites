import os
import json
import requests
import time
import asyncio
from dotenv import load_dotenv
from database.database import *

os.chdir(os.path.dirname(__file__))
load_dotenv()
headers = {
    "Cookie": f".ROBLOSECURITY={os.environ["cookie"]}"
}

def clear():
    print("\033[2J\033[3J\033[H", end="")

def save_data(data, file):
    data_json = json.dumps(data, indent=2)
    with open(f"./data/{file}", mode="w") as f:
        f.write(data_json)

def load_data(
    file: str,
    no_exist_data: dict | list | None = {},
    no_exist_ok: bool = True,
    no_exist_message: str = "",
) -> dict | list:
    if os.path.exists(f"./data/{file}"):
        with open(f"./data/{file}") as f:
            return json.loads(f.read())
    elif no_exist_ok:
        return no_exist_data
    elif not no_exist_ok and no_exist_message != "":
        print(f"{no_exist_message}")
        raise SystemExit
    return {}

def convert_cached_ids():
    cached_ids = load_data("cached_ids.json", {}, False, "You don't have any cached data.")
    if "place_id_cache_temp" not in cached_ids:
        cached_ids["place_id_cache_temp"] = {}
    if "place_id_cache" not in cached_ids:
        cached_ids["place_id_cache"] = {}
    if "universe_id_cache" not in cached_ids:
        cached_ids["universe_id_cache"] = []

    clear()
    print("[Roblox Invites Migration Tool]")
    print("Converting place ID cache...")
    total_entries = len(list(cached_ids["indexes"]))
    current_entry = 1
    for place_id, universe_id in cached_ids["indexes"].items():
        if place_id not in cached_ids["place_id_cache_temp"]:
            max_players = 2
            if str(universe_id) in cached_ids["caches"]:
                if "max_players" in cached_ids["caches"][str(universe_id)]:
                    if place_id in cached_ids["caches"][str(universe_id)]["max_players"]:
                        max_players = cached_ids["caches"][str(universe_id)]["max_players"][place_id]
                        print(f"Saved {current_entry}/{total_entries} (local - max {max_players} players)")
                    else:
                        max_players_req = requests.get(f"https://games.roblox.com/v1/games/{place_id}/servers/0?sortOrder=2&excludeFullGames=false&limit=10", headers=headers).json()
                        try:
                            max_players = max_players_req["data"][0]["maxPlayers"]
                        except IndexError:
                            max_players = 1
                        except KeyError:
                            if max_players_req["errors"][0]["code"] == 1 and max_players_req["errors"][0]["message"] == "The place is invalid.":
                                max_players = 1
                            else:
                                print(max_players_req)
                                exit()
                        print(f"Saved {current_entry}/{total_entries} (request - max {max_players} players)")
                        time.sleep(0.5)
                else:
                    max_players_req = requests.get(f"https://games.roblox.com/v1/games/{place_id}/servers/0?sortOrder=2&excludeFullGames=false&limit=10", headers=headers).json()
                    try:
                        max_players = max_players_req["data"][0]["maxPlayers"]
                    except IndexError:
                        max_players = 1
                    except KeyError:
                        if max_players_req["errors"][0]["code"] == 1 and max_players_req["errors"][0]["message"] == "The place is invalid.":
                            max_players = 1
                        else:
                            print(max_players_req)
                            exit()
                    print(f"Saved {current_entry}/{total_entries} (request - max {max_players} players)")
                    time.sleep(0.5)
            cached_ids["place_id_cache_temp"][place_id] = {
                "universe_id": universe_id,
                "max_players": max_players
            }
            save_data(cached_ids, "cached_ids.json")
        current_entry += 1

    print("\nFinished converting Place ID cache items")
    place_id_cache = []
    for place_id, cache in cached_ids["place_id_cache_temp"].items():
        place_id_cache += [(
            int(place_id),
            int(cache["universe_id"]),
            int(cache["max_players"])
        )]
    cached_ids["place_id_cache"] = place_id_cache
    print("Place ID cache converted")

    print("\nConverting Universe ID cache...")
    cache["universe_id_cache"] = []
    for universe_id, cache in cached_ids["caches"].items():
        if "last_update" in cache:
            month, day, year = cache["last_update"][0], cache["last_update"][1], cache["last_update"][2]
        else:
            month, day, year = 1, 1, 1970
        cached_ids["universe_id_cache"] += [(
            int(universe_id),
            int(cache["root_place_id"]),
            cache["name"],
            month,
            day,
            year,
        )]
    save_data(cached_ids, "cached_ids.json")
    print("Universe ID cache converted and cached_ids saved to disk")
    input("\nPress ENTER to return to the main menu.")

def convert_stats():
    stats = load_data("stats.json", {}, False, "You don't have any statistics data.")
    clear()
    print("[Roblox Invites Migration Tool]")
    print("Converting statistics data...")

    for user_id, data in stats.items():
        if user_id in ["total_playtimes", "game_playtimes"]:
            continue
        if data["currently_playing"] != {}:
            currently_playing = data["currently_playing"]
            if str(currently_playing["root_place_id"]) in data["games_playtime"]:
                data["games_playtime"][str(currently_playing["root_place_id"])]["playtime"] += round(time.time() - currently_playing["start"])
            else:
                data["games_playtime"][str(currently_playing["root_place_id"])] = {"playtime": round(time.time() - currently_playing["start"])}
        data["currently_playing"] = {}
    if os.path.exists("./server/old_user_presences.json"):
        os.remove("./server/old_user_presences.json")

    stats["total_playtimes"] = []
    stats["game_playtimes"] = []
    for user_id, user_statistics in stats.items():
        if user_id in ["total_playtimes", "game_playtimes"]:
            continue
        stats["total_playtimes"] += [(
            int(user_id),
            user_statistics["total_playtime"]
        )]
        for place_id, playtime in stats[user_id]["games_playtime"].items():
            stats["game_playtimes"] += [(
                int(user_id),
                int(place_id),
                playtime["playtime"]
            )]
    save_data(stats, "stats.json")
    print("Done converting statistics data and stats saved to disk")
    input("Press ENTER to return to the main menu.")

async def upload_caches():
    cached_ids = load_data("cached_ids.json", {}, False, "You don't have any cached data.")
    if "place_id_cache" not in cached_ids or "universe_id_cache" not in cached_ids:
        return

    database = Database()
    await database.initalize()
    pool = database.pool

    async with pool.acquire() as conn:
        await conn.executemany("""
            INSERT INTO place_id_cache (place_id, universe_id, max_players)
            VALUES ($1, $2, $3)
            ON CONFLICT (place_id)
            DO NOTHING
        """, cached_ids["place_id_cache"])

        await conn.executemany("""
            INSERT INTO universe_id_cache (universe_id, root_place_id, game_name, month_last_updated, day_last_updated, year_last_updated)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (universe_id)
            DO NOTHING
        """, cached_ids["universe_id_cache"])

async def upload_stats():
    stats = load_data("stats.json")
    if "total_playtimes" not in stats or "game_playtimes" not in stats:
        return

    database = Database()
    await database.initalize()
    pool = database.pool

    async with pool.acquire() as conn:
        await conn.executemany("""
            INSERT INTO total_playtimes (user_id, total_playtime)
            VALUES ($1, $2)
            ON CONFLICT (user_id)
            DO NOTHING
        """, stats["total_playtimes"])

        await conn.executemany("""
            INSERT INTO game_playtimes (user_id, place_id, playtime)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id, place_id)
            DO NOTHING
        """, stats["game_playtimes"])

async def upload_users():
    users = load_data("users.json", {}, False, "You don't have any user data.")
    users_upload = []
    subscriptions_upload = []

    clear()
    print("[Roblox Invites Migrate Tool]")
    print("Roblox Invites previously ran on a single-server architecture.")
    guild_id = int(input("What Discord server will the following users be added to? "))
    print("")

    for i, (user_id, data) in enumerate(list(users.items()), start=1):
        discord_id = int(input(f"({i}/{len(list(users))}) Enter the Discord ID for {data["display_name"]} (@{data["username"]}): "))
        users_upload += [(
            int(user_id),
            discord_id,
            data["username"],
            data["display_name"]
        )]
        subscriptions_upload += [(
            guild_id,
            int(user_id)
        )]
    database = Database()
    await database.initalize()
    pool = database.pool

    async with pool.acquire() as conn:
        await conn.executemany("""
            INSERT INTO users (user_id, discord_id, username, display_name)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id)
            DO NOTHING
        """, users_upload)

        await conn.executemany("""
            INSERT INTO subscriptions (guild_id, user_id)
            VALUES ($1, $2)
            ON CONFLICT (guild_id, user_id)
            DO NOTHING
        """, subscriptions_upload)

async def upload_custom_titles():
    custom_titles = load_data("custom_titles.json", {}, False, "You don't have any custom titles.")

    clear()
    print("[Roblox Invites Migrate Tool]")
    print("Roblox Invites previously ran on a single-server architecture.")
    guild_id = int(input("What Discord server will the saved custom titles be added to? "))

    ct_upload = []
    for universe_id, title in custom_titles["titles"].items():
        ct_upload += [(
            guild_id,
            int(universe_id),
            title["title"],
            title["color"],
            title["game"],
            int(title["place_id"])
        )]

    database = Database()
    await database.initalize()
    pool = database.pool

    async with pool.acquire() as conn:
        await conn.executemany("""
            INSERT INTO custom_titles (guild_id, universe_id, title, color, game_name, root_place_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (guild_id, universe_id)
            DO NOTHING
        """, ct_upload)

while True:
    clear()
    print("[Roblox Invites Migration Tool]")
    print("Migrate your RI data over to PostgreSQL when v2.0.0 releases!")
    print("Converting cache data may take a while if you've used a legacy version of RI and don't have all your data cached.")
    print("Do not run Roblox Invites while converting data.")

    print("\nCommands:")
    print("- cache - Saves cache data to prepare for upload to database")
    print("- stats - Saves statistics data to prepare for upload to database")
    print("- upload - Uploads everything to database")
    print("- upload_cache - Uploads cache to database")
    print("- upload_stats - Uploads stats to database")
    print("- upload_users - Uploads users to database")
    print("- upload_ct - Uploads custom titles to database")

    command = input("\nType a command: ").lower().strip()

    if command == "cache":
        convert_cached_ids()
    elif command == "stats":
        convert_stats()
    elif command == "upload_cache":
        asyncio.run(upload_caches())
    elif command == "upload_stats":
        asyncio.run(upload_stats())
    elif command == "upload_users":
        asyncio.run(upload_users())
    elif command == "upload_ct":
        asyncio.run(upload_custom_titles())
    elif command == "upload":
        asyncio.run(upload_caches())
        asyncio.run(upload_stats())
        asyncio.run(upload_custom_titles())
        asyncio.run(upload_users())