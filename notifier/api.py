import aiohttp
from datetime import datetime
from database.database import *
from aiohttp_retry import RetryClient, ExponentialRetry

class API:
    def __init__(self, headers):
        self.session = None
        self.retry_client = None
        self.database = None
        self.pool = None
        self.headers = headers

    async def start(self):
        self.retry_options = ExponentialRetry(attempts=5, start_timeout=0.75, statuses={429, 500, 502, 503, 504})
        self.session = aiohttp.ClientSession()
        self.retry_client = RetryClient(client_session=self.session, retry_options=self.retry_options)
    
    async def close(self):
        await self.retry_client.close()

    async def cache_id(self, place_id):
        place_id = int(place_id)
        if not await self.check_cached_place_id(place_id):
            universe_id = await self.get_misc(f"https://apis.roblox.com/universes/v1/places/{place_id}/universe")
            universe_id = universe_id["universeId"]
            
            game_data = await self.get_misc(f"https://games.roblox.com/v1/games?universeIds={universe_id}")
            game_name = game_data["data"][0]["name"]
            root_place_id = game_data["data"][0]["rootPlaceId"]
           
            server_data = await self.get_misc(f"https://games.roblox.com/v1/games/{place_id}/servers/0?sortOrder=2&excludeFullGames=false&limit=10")
            if len(server_data["data"]) > 0:
                max_players = server_data["data"][0]["maxPlayers"]
            else:
                max_players = 2

            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO place_id_cache (place_id, universe_id, max_players)
                    VALUES ($1, $2, $3)
                """, place_id, universe_id, max_players)

            if not await self.check_cached_universe_id(universe_id):
                now = datetime.now()
                async with self.pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO universe_id_cache (universe_id, root_place_id, game_name, month_last_updated, day_last_updated, year_last_updated)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """, universe_id, root_place_id, game_name, now.month, now.day, now.year)

    async def check_cached_place_id(self, place_id):
        if place_id == None:
            return False

        async with self.pool.acquire() as conn:
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1
                    FROM place_id_cache
                    WHERE place_id = $1
                )
            """, place_id)
            return exists

    async def check_cached_universe_id(self, universe_id):
        if universe_id == None:
            return False

        async with self.pool.acquire() as conn:
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1
                    FROM universe_id_cache
                    WHERE universe_id = $1
                )
            """, universe_id)
            return exists

    async def get_cached_data(self, universe_id):
        async with self.pool.acquire() as conn:
            data = await conn.fetchrow("""
                SELECT *
                FROM universe_id_cache
                WHERE universe_id = $1
            """, universe_id)
            return data

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

        await self.cache_id(place_id)
        async with self.pool.acquire() as conn:
            universe_id = await conn.fetchval("""
                SELECT universe_id
                FROM place_id_cache
                WHERE place_id = $1
            """, place_id)
            return universe_id

    async def get_root_place_id(self, place_id):
        if place_id == None:
            return None
        
        await self.cache_id(place_id)
        universe_id = await self.get_universe_id(place_id)
        cached_data = await self.get_cached_data(universe_id)
        return cached_data["root_place_id"]

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

        await self.cache_id(place_id)
        universe_id = await self.get_universe_id(place_id)
        cached_data = await self.get_cached_data(universe_id)
        return cached_data["game_name"]
    
    async def get_max_players(self, place_id):
        if place_id == None:
            return None

        max_players = 2
        await self.cache_id(place_id)
        async with self.pool.acquire() as conn:
            max_players = await conn.fetchval("""
                SELECT max_players
                FROM place_id_cache
                WHERE place_id = $1
            """, place_id)
        return max_players

    async def get_user_data(self, usernames):
        async with self.retry_client.post("https://users.roblox.com/v1/usernames/users", json={"usernames": usernames}, headers=self.headers) as response:
            response.raise_for_status()
            user_data = await response.json()
            return user_data
    
    async def get_cached_games(self, guild):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT user_id
                FROM subscriptions
                WHERE guild_id = $1
            """, guild.id)
            user_ids = [row["user_id"] for row in rows]

            rows = await conn.fetch("""
                SELECT place_id
                FROM game_playtimes
                WHERE user_id = ANY($1)
            """, user_ids)
            place_ids = [row["place_id"] for row in rows]

            rows = await conn.fetch("""
                SELECT *
                FROM universe_id_cache
                WHERE root_place_id = ANY($1)
            """, place_ids)
            return rows