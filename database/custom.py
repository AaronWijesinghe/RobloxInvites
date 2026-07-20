from styling.formatting import *

class CGTManager:
    def __init__(self, database, api):
        self.database = database
        self.api = api
        self.pool = self.database.pool

    async def get_custom_title(self, guild, universe_id):
        if await self.check_custom_title(guild, universe_id):
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT *
                    FROM custom_titles
                    WHERE guild_id = $1
                    AND universe_id = $2
                """, guild.id, universe_id)
            return row

    async def check_custom_title(self, guild, universe_id):
        async with self.pool.acquire() as conn:
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1
                    FROM custom_titles
                    WHERE guild_id = $1
                    AND universe_id = $2
                )
            """, guild.id, universe_id)
            return exists

    async def add_custom_title(self, place_id, title, hex_color, guild):
        hex_color = hex_color.lower().replace("#", "")

        if not "{0}" in title:
            return "You must include `{0}` in your Custom Title to represent the user's display name."
        elif "\\" in title:
            return "Do not try to break the bot. :)"
        elif "<@" in title:
            return "Do not try to ping other users with Custom Titles."
        elif len(hex_color) != 6:
            return "Invalid hex color."

        success = await self.api.cache_id(place_id)
        if not success:
            return "This game doesn't exist."
        universe_id = await self.api.get_universe_id(place_id)
        game_name = await self.api.get_game_name(place_id)
        root_place_id = await self.api.get_root_place_id(place_id)

        print(guild.id, universe_id, title, hex_color, game_name, root_place_id)
        async with self.pool.acquire() as conn:
            added = await conn.fetchval("""
                INSERT INTO custom_titles (guild_id, universe_id, title, color, game_name, root_place_id)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (guild_id, universe_id)
                DO NOTHING
                RETURNING guild_id
            """, guild.id, universe_id, title, hex_color, game_name, root_place_id)
            if added:
                return True
            else:
                return "This game was already added.\nIt must be removed from the Custom Titles list by a server admin."

    async def remove_custom_title(self, place_id, guild):
        universe_id = await self.api.get_universe_id(place_id)

        if await self.check_custom_title(guild, universe_id):
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    DELETE FROM custom_titles
                    WHERE guild_id = $1
                    AND universe_id = $2
                """, guild.id, universe_id)
            return True

    async def get_cgt_games(self, guild):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT root_place_id
                FROM custom_titles
                WHERE guild_id = $1
            """, guild.id)
            place_ids = [row["root_place_id"] for row in rows]

            rows = await conn.fetch("""
                SELECT *
                FROM universe_id_cache
                WHERE root_place_id = ANY($1)
            """, place_ids)
            return rows