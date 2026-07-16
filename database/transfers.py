class TransferManager:
    def __init__(self, database):
        self.database = database
        self.pool = self.database.pool

    async def get_transfer(self, user_id):
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT *
                    FROM transfers
                    WHERE user_id = $1
                """, user_id)
            return row
        except:
            return {}
    
    async def check_transfer(self, user_id):
        async with self.pool.acquire() as conn:
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1
                    FROM transfers
                    WHERE user_id = $1
                )
            """, user_id)
            return exists

    async def add_transfer(self, user_id, old_place_id, old_game_instance_id):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO transfers (user_id, old_game_instance_id, old_place_id)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    old_game_instance_id = EXCLUDED.old_game_instance_id,
                    old_place_id = EXCLUDED.old_place_id
            """, user_id, old_game_instance_id, old_place_id)
        return True

    async def remove_transfer(self, user_id):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                DELETE FROM transfers
                WHERE user_id = $1
            """, user_id)
        return True

    async def get_guild_users(self, guild_id):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT *
                FROM subscriptions
                WHERE guild_id = $1
            """, guild_id.id)
        
        user_ids = [row["user_id"] for row in rows]
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT *
                FROM users
                WHERE user_id = ANY($1)
            """, user_ids)

        return rows