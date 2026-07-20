class BlacklistManager:
    def __init__(self, database, api):
        self.database = database
        self.api = api
        self.pool = self.database.pool

    async def check_blacklist(self, guild, place_id):
        async with self.pool.acquire() as conn:
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1
                    FROM blacklist
                    WHERE guild_id = $1
                    AND place_id = $2
                )
            """, guild.id, place_id)
            return exists

    async def add_blacklist(self, guild, place_id, game_name):
        if not await self.check_blacklist(guild, place_id):
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO blacklist (guild_id, place_id, game_name)
                    VALUES ($1, $2, $3)
                """, guild.id, place_id, game_name)
            return True
        else:
            return False

    async def remove_blacklist(self, guild, place_id):
        if await self.check_blacklist(guild, place_id):
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    DELETE FROM blacklist
                    WHERE guild_id = $1
                    AND place_id = $2
                """, guild.id, place_id)
            return True
        else:
            return False

    async def get_blacklisted_games(self, guild):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT *
                FROM blacklist
                WHERE guild_id = $1
            """, guild.id)
            return rows