import aiohttp
import asyncio
from datetime import datetime
from database.database import *
from aiohttp_retry import RetryClient, ExponentialRetry

class RobloxAPI:
    def __init__(self, headers):
        self.session = None
        self.retry_client = None
        self.headers = headers
    
    async def start(self):
        self.retry_options = ExponentialRetry(attempts=5, start_timeout=0.75, statuses={429, 500, 502, 503, 504})
        self.session = aiohttp.ClientSession()
        self.retry_client = RetryClient(client_session=self.session, retry_options=self.retry_options)
    
    async def close(self):
        await self.retry_client.close()

    async def get_misc(self, url):
        async with self.retry_client.get(url, headers=self.headers) as response:
            response.raise_for_status()
            data = await response.json()
            return data

    async def post_misc(self, url, json):
        async with self.retry_client.post(url, json=json, headers=self.headers) as response:
            response.raise_for_status()
            data = await response.json()
            return data

    async def get_universe_id(self, place_id):
        if place_id == None:
            return None

        universe_id = await self.get_misc(f"https://apis.roblox.com/universes/v1/places/{place_id}/universe")
        universe_id = universe_id["universeId"]

        return universe_id

    async def get_root_place_id(self, place_id):
        if place_id == None:
            return None

        universe_id = await self.get_universe_id(place_id)
        game_data = await self.get_misc(f"https://games.roblox.com/v1/games?universeIds={universe_id}")
        root_place_id = game_data["data"][0]["rootPlaceId"]

        return root_place_id

    async def check_root_place_id(self, place_id_1, place_id_2):
        rpid_1 = await self.get_root_place_id(place_id_1)
        rpid_2 = await self.get_root_place_id(place_id_2)
        return rpid_1 == rpid_2

    async def get_presences(self, user_ids):
        async with self.retry_client.post("https://presence.roblox.com/v1/presence/users/", data={"userIDs": user_ids}, headers=self.headers) as response:
            response.raise_for_status()
            return await response.json()
    
    async def get_game_name(self, place_id):
        if place_id == None:
            return None

        game_data = await self.get_misc(f"https://games.roblox.com/v1/games?universeIds={universe_id}")
        game_name = game_data["data"][0]["name"]

        return game_name   
    
    async def get_max_players(self, place_id):
        if place_id == None:
            return None

        max_players = 2
        game_data = await self.get_misc(f"https://games.roblox.com/v1/games/{place_id}/servers/0?sortOrder=2&excludeFullGames=false&limit=10")
        if len(game_data["data"]) > 0:
            max_players = game_data["data"][0]["maxPlayers"]
        
        return max_players

    async def get_user_data(self, usernames):
        async with self.retry_client.post("https://users.roblox.com/v1/usernames/users", json={"usernames": usernames}, headers=self.headers) as response:
            response.raise_for_status()
            user_data = await response.json()
            return user_data