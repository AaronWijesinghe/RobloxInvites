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

    async def get_guild_users(self, guild):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(f"""
                SELECT u.*
                FROM users AS u
                JOIN subscriptions AS s
                    ON u.user_id = s.user_id
                WHERE s.guild_id = $1
            """, guild.id)

        return rows

    async def get_guild_user_ids(self, guild):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT user_id
                FROM subscriptions
                WHERE guild_id = $1
                ORDER BY user_id
            """, guild.id)
        
        user_ids = [row["user_id"] for row in rows]
        return user_ids

    async def get_user_from_discord_id(self, discord_user):
        async with self.pool.acquire() as conn:
            user_id = await conn.fetchval("""
                SELECT user_id
                FROM users
                WHERE discord_id = $1
            """, discord_user.id)
            return user_id

    async def get_all_users(self):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT *
                FROM users
                ORDER BY user_id
            """)
        users = {
            row["user_id"]: row
            for row in rows
        }
        return users

    async def get_all_user_ids(self):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT user_id
                FROM users
                ORDER BY user_id
            """)
        user_ids = [row["user_id"] for row in rows]
        return user_ids

    async def add_user(self, username, discord_user, guild):
        req = await self.api.post_misc("https://users.roblox.com/v1/usernames/users", json={"usernames": [username]})
        if "data" not in req:
            return "This user doesn't exist."
        if len(req["data"]) == 0:
            return "This user doesn't exist."

        user_id = req["data"][0]["id"]
        username = req["data"][0]["name"]
        display_name = req["data"][0]["displayName"]

        async with self.pool.acquire() as conn:
            user_exists_in_ri = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1
                    FROM users
                    WHERE user_id = $1
                )
            """, user_id)
            user_exists_in_guild = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1
                    FROM subscriptions
                    WHERE guild_id = $1
                    AND user_id = $2
                )
            """, guild.id, user_id)
            owner_account_id = await conn.fetchval("""
                SELECT discord_id
                FROM users
                WHERE user_id = $1
            """, user_id)
            if not user_exists_in_ri:
                user_data = await self.api.get_misc(f"https://users.roblox.com/v1/users/{user_id}")
                if user_data["description"].lower().strip() != "i confirm that i am joining the invites program.":
                    return f"You must verify that the following account (@{username}) is yours.\nPlease set `I confirm that I am joining the Invites program.` as your Roblox account description and retry again."
            elif user_exists_in_guild:
                return f"This user already exists in this server."
            else:
                if owner_account_id != discord_user.id:
                    return "This account has already been linked by someone else."

            await conn.execute("""
                INSERT INTO users (user_id, discord_id, username, display_name)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    username = EXCLUDED.username,
                    display_name = EXCLUDED.display_name
            """, user_id, discord_user.id, username, display_name)

            await conn.execute("""
                INSERT INTO subscriptions (guild_id, user_id)
                VALUES ($1, $2)
                ON CONFLICT (guild_id, user_id)
                DO NOTHING
            """, guild.id, user_id)
        return True

    async def remove_user(self, discord_user, guild):
        async with self.pool.acquire() as conn:
            user_id = await conn.fetchval("""
                SELECT user_id
                FROM users
                WHERE discord_id = $1
            """, discord_user.id)
            if user_id is None:
                return False

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

            await conn.execute("""
                DELETE FROM presences
                WHERE user_id = ANY($1)
            """, deleted_user_ids)

            await conn.execute("""
                DELETE FROM old_presences
                WHERE user_id = ANY($1)
            """, deleted_user_ids)

    async def update_user_info(self, discord_user):
        async with self.pool.acquire() as conn:
            user_id = await conn.fetchval("""
                SELECT user_id
                FROM users
                WHERE discord_id = $1
            """, discord_user.id)
            if user_id is None:
                return f"You don't have a Roblox account associated with Roblox Invites.\nAdd one with `/user add`!"

        req = await self.api.post_misc("https://users.roblox.com/v1/users", json={"userIds": [user_id]})
        if "data" not in req:
            return "Couldn't update your user info."
        if len(req["data"]) == 0:
            return "Couldn't update your user info."
        username = req["data"][0]["name"]
        display_name = req["data"][0]["displayName"]

        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (user_id, discord_id, username, display_name)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    username = EXCLUDED.username,
                    display_name = EXCLUDED.display_name
            """, user_id, discord_user.id, username, display_name)
        return True