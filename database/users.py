class UserManager:
    def __init__(self, database, api):
        self.database = database
        self.api = api
        self.pool = self.database.pool

    async def get_display_name(self, user_id):
        async with self.pool.acquire() as conn:
            return await conn.fetchval("""
                SELECT display_name
                FROM users
                WHERE user_id = $1
            """, user_id)

    async def get_username(self, user_id):
        async with self.pool.acquire() as conn:
            return await conn.fetchval("""
                SELECT username
                FROM users
                WHERE user_id = $1
            """, user_id)

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

    async def get_guild_user_ids(self, guild_id):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT *
                FROM subscriptions
                WHERE guild_id = $1
            """, guild_id.id)
        
        user_ids = [row["user_id"] for row in rows]
        return user_ids

    async def get_all_users(self):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT *
                FROM users
            """)
        users = {
            rows[i]["user_id"]: {
                "username": rows[i]["username"],
                "display_name": rows[i]["display_name"]
            }
            for i in range(len(rows))
        }
        return users

    async def get_all_user_ids(self):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT user_id
                FROM users
            """)
        user_ids = [row["user_id"] for row in rows]
        return user_ids

    async def add_user(self, username, guild):
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
                ON CONFLICT (user_id)
                DO UPDATE SET
                    username = EXCLUDED.username,
                    display_name = EXCLUDED.display_name
            """, user_id, username, display_name)

            await conn.execute("""
                INSERT INTO subscriptions (guild_id, user_id)
                VALUES ($1, $2)
                ON CONFLICT (guild_id, user_id)
                DO NOTHING
            """, guild.id, user_id)
        return True

    async def remove_deleted_users(self):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT user_id
                FROM users
                WHERE erased = 1
            """)
            if rows is None:
                return
            deleted_user_ids = [row["user_id"] for row in rows]

            await conn.execute("""
                DELETE FROM subscriptions
                WHERE user_id = ANY($1)
            """, deleted_user_ids)

            await conn.execute("""
                DELETE FROM users
                WHERE user_id = ANY($1)
            """, deleted_user_ids)

            await conn.execute("""
                DELETE FROM currently_playing
                WHERE user_id = ANY($1)
            """, deleted_user_ids)

            await conn.execute("""
                DELETE FROM game_playtimes
                WHERE user_id = ANY($1)
            """, deleted_user_ids)

            await conn.execute("""
                DELETE FROM total_playtimes
                WHERE user_id = ANY($1)
            """, deleted_user_ids)

    async def remove_user(self, user_id, guild):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                DELETE FROM subscriptions
                WHERE guild_id = $1
                AND user_id = $2
            """, guild.id, user_id)

            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1
                    FROM subscriptions
                    WHERE user_id = $1
                )
            """, user_id)

            if not exists:
                await self.remove_user_global(user_id)
        return True

    async def remove_user_global(self, user_id):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE users
                SET erased = 1
                WHERE user_id = $1
            """, user_id)