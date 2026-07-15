class BlacklistManager:
    def __init__(self, database, api):
        self.database = database
        self.api = api
        self.pool = self.database.pool

    async def get_user(self, user_id):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("""
                SELECT *
                FROM users
                WHERE user_id = $1
            """, user_id)

    async def get_guild_users(self, guild_id):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT *
                FROM subscriptions
                WHERE guild_id = $1
            """, guild_id)
        
        user_ids = [row["user_id"] for row in rows]
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT *
                FROM users
                WHERE user_id = ANY($1)
            """, user_ids)

        return rows

    async def add_blacklist(self, guild_id, place_id, game_name):
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO blacklist (guild_id, place_id, game_name)
                    VALUES ($1, $2, $3)
                """, guild_id, place_id, game_name)
        except:
            return False
        return True

    async def remove_blacklist(self, guild_id, place_id):
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    DELETE FROM blacklist (guild_id, place_id, game_name)
                    WHERE guild_id = $1
                    AND place_id = $2
                """, guild_id, place_id)
        except:
            return False
        return True