class UserManager:
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

    async def get_guild_user_ids(self, guild_id):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT *
                FROM subscriptions
                WHERE guild_id = $1
            """, guild_id)
        
        user_ids = [row["user_id"] for row in rows]
        return user_ids

    async def get_all_users(self):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT *
                FROM users
            """)
        return rows

    async def get_all_user_ids(self):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT user_id
                FROM users
            """)
        user_ids = [row["user_id"] for row in rows]
        return user_ids

    async def add_user(self, username):
        req = await self.api.post_misc("https://users.roblox.com/v1/usernames/users", json={"usernames": [username]})
        if "data" not in req:
            return False
        if len(req["data"]) == 0:
            return False

        user_id = req["data"][0]["id"]
        username = req["data"][0]["name"]
        display_name = req["data"][0]["displayName"]
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (user_id, username, display_name)
                VALUES ($1, $2, $3)
                DO UPDATE SET
                    username = EXCLUDED.username
                    display_name = EXCLUDED.display_name
            """, user_id, username, display_name)
        return True

    async def remove_user(self, user_id):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                DELETE FROM users
                WHERE user_id = $1
            """, user_id)
        return True