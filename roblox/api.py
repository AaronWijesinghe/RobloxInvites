import aiohttp
import asyncio
from datetime import datetime
from storage.database import *
from aiohttp_retry import RetryClient, ExponentialRetry

class RobloxAPI:
    def __init__(self):
        self.session = None
        self.retry_client = None
        self.cache = load_data("cached_ids.json", {"indexes": [], "caches": {}})
    
    async def start(self):
        self.retry_options = ExponentialRetry(attempts=5, start_timeout=0.75, statuses={429, 500, 502, 503, 504})
        self.session = aiohttp.ClientSession()
        self.retry_client = RetryClient(client_session=self.session, retry_options=self.retry_options)
    
    async def close(self):
        await self.retry_client.close()

    async def cache_id(self, int_place_id: int) -> None:
        for key in ["indexes", "caches"]:
            if key not in self.cache:
                self.cache[key] = {}

        place_id = str(int_place_id)
        if place_id not in self.cache["indexes"]:
            universe_id = await self.get_misc(f"https://apis.roblox.com/universes/v1/places/{place_id}/universe")
            universe_id = universe_id["universeId"]
            game_data = await self.get_misc(f"https://games.roblox.com/v1/games?universeIds={universe_id}")
            game_name = game_data["data"][0]["name"]
            game_root_place_id = game_data["data"][0]["rootPlaceId"]
            self.cache["indexes"][place_id] = universe_id
            self.cache["caches"][str(universe_id)] = {
                "root_place_id": game_root_place_id,
                "name": game_name,
                "last_update": [datetime.now().month, datetime.now().day, datetime.now().year],
                "max_players": {}
            }
            save_data(self.cache, "cached_ids.json")

    async def cache_game_name(self, int_place_id: int) -> None:
        place_id = str(int_place_id)
        universe_id = self.cache["indexes"][place_id]
        game_data = await self.get_misc(f"https://games.roblox.com/v1/games?universeIds={universe_id}")
        game_name = game_data["data"][0]["name"]
        self.cache["caches"][str(universe_id)]["name"] = game_name
        self.cache["caches"][str(universe_id)]["last_update"] = [datetime.now().month, datetime.now().day, datetime.now().year]
        save_data(self.cache, "cached_ids.json")

    async def cache_max_players(self, int_place_id: int) -> None:
        place_id = str(int_place_id)
        universe_id = self.cache["indexes"][place_id]
        game_data = await self.get_misc(f"https://games.roblox.com/v1/games/{place_id}/servers/0?sortOrder=2&excludeFullGames=false&limit=10")
        max_players = game_data["data"][0]["maxPlayers"]
        self.cache["caches"][str(universe_id)]["max_players"][place_id] = max_players
        save_data(self.cache, "cached_ids.json")

    async def get_misc(self, url):
        async with self.retry_client.get(url) as response:
            response.raise_for_status()
            data = await response.json()
            return data

    async def get_universe_id(self, place_id):
        if place_id not in self.cache["indexes"]:
            await self.cache_id(place_id)
        if str(place_id) in self.cache["indexes"]:
            return self.cache["indexes"][str(place_id)]

    async def get_root_place_id(self, place_id):
        if place_id == None:
            return None

        if place_id not in self.cache["indexes"]:
            await self.cache_id(place_id)
        if str(place_id) in self.cache["indexes"]:
            universe_id = self.cache["indexes"][str(place_id)]
            if "root_place_id" in self.cache["caches"][str(universe_id)]:
                return self.cache["caches"][str(universe_id)]["root_place_id"]

    async def check_root_place_id(self, place_id_1, place_id_2):
        rpid_1 = await self.get_root_place_id(place_id_1)
        rpid_2 = await self.get_root_place_id(place_id_2)
        return rpid_1 == rpid_2

    async def get_presences(self, user_ids, headers):
        async with self.retry_client.post("https://presence.roblox.com/v1/presence/users/", data={"userIDs": user_ids}, headers=headers) as response:
            response.raise_for_status()
            return await response.json()
    
    async def get_game_name(self, place_id):
        if place_id not in self.cache["indexes"]:
            await self.cache_id(place_id)
        if str(place_id) in self.cache["indexes"]:
            current_day = [datetime.now().month, datetime.now().day, datetime.now().year]
            universe_id = self.cache["indexes"][str(place_id)]
            if "name" in self.cache["caches"][str(universe_id)]:
                if "last_update" not in self.cache["caches"][str(universe_id)]:
                    await self.cache_game_name(place_id)
                elif self.cache["caches"][str(universe_id)]["last_update"] != current_day:
                    await self.cache_game_name(place_id)
                return self.cache["caches"][str(universe_id)]["name"]
        return None
    
    async def get_max_players(self, place_id):
        if place_id not in self.cache["indexes"]:
            await self.cache_id(place_id)
        if str(place_id) in self.cache["indexes"]:
            universe_id = self.cache["indexes"][str(place_id)]
            if "name" in self.cache["caches"][str(universe_id)]:
                if "max_players" not in self.cache["caches"][str(universe_id)]:
                    self.cache["caches"][str(universe_id)]["max_players"] = {}
                if str(place_id) not in self.cache["caches"][str(universe_id)]["max_players"]:
                    await self.cache_max_players(place_id)
                return self.cache["caches"][str(universe_id)]["max_players"][str(place_id)]
        return 2

    async def get_user_data(self, usernames):
        async with self.retry_client.post("https://users.roblox.com/v1/usernames/users", json={"usernames": usernames}) as response:
            response.raise_for_status()
            user_data = await response.json()
            return user_data