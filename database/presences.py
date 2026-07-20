class PresenceManager:
    def __init__(self, database, api, user_manager):
        self.database = database
        self.api = api
        self.pool = self.database.pool
        self.user_manager = user_manager

    async def save_presences(self, presence_type):
        user_ids = await self.user_manager.get_all_user_ids()
        if presence_type == "current":
            presences = await self.api.get_presences(user_ids)
            presence_records = [
                (
                    user_ids[i],
                    presences["userPresences"][i]["gameId"],
                    presences["userPresences"][i]["placeId"],
                    presences["userPresences"][i]["userPresenceType"]
                )
                for i in range(len(presences["userPresences"]))
            ]
        elif presence_type == "old":
            presence_records = await self.get_all_presences_unfiltered()

        async with self.pool.acquire() as conn:
            await conn.executemany(f"""
                INSERT INTO {"old_presences" if presence_type == "old" else "presences"} (user_id, game_instance_id, place_id, user_status)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    game_instance_id = EXCLUDED.game_instance_id,
                    place_id = EXCLUDED.place_id,
                    user_status = EXCLUDED.user_status
            """, presence_records)

    async def get_presence(self, user_id):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("""
                SELECT *
                FROM presences
                WHERE user_id = $1
            """, user_id)

    async def get_guild_presences(self, guild, presence_type):
        table = "old_presences" if presence_type == "old" else "presences"
    
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(f"""
                SELECT p.*
                FROM {table} AS p
                JOIN subscriptions AS s
                    ON p.user_id = s.user_id
                WHERE s.guild_id = $1
            """, guild.id)
        
        if len(rows) > 0:
            presences = {
                row["user_id"]: row
                for row in rows
            }
        else:
            presences = {
                row["user_id"]: {
                    "game_instance_id": None,
                    "place_id": None,
                    "user_status": 0
                }
                for row in rows
            }

        return presences

    async def get_all_presences(self, presence_type):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT *
                FROM users
            """)
        
        user_ids = [row["user_id"] for row in rows]
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(f"""
                SELECT *
                FROM {"old_presences" if presence_type == "old" else "presences"}
                WHERE user_id = ANY($1)
            """, user_ids)
        
        presences = {
            row["user_id"]: row
            for row in rows
        }

        return presences
    
    async def get_all_presences_unfiltered(self):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT *
                FROM users
                ORDER BY user_id
            """)
        
        user_ids = [row["user_id"] for row in rows]
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(f"""
                SELECT *
                FROM presences
                WHERE user_id = ANY($1)
                ORDER BY user_id
            """, user_ids)

        return rows

    async def check_joins(self, guild, user_id, place_id, game_instance_id):
        joined = []
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(f"""
                SELECT user_id
                FROM presences
                WHERE place_id = $1
                AND game_instance_id = $2
                AND NOT user_id = $3
            """, place_id, game_instance_id, user_id)
            guild_users = await self.user_manager.get_guild_users(guild)
            joined_user_ids = [row["user_id"] for row in rows]

        for guild_user in guild_users:
            if guild_user["user_id"] in joined_user_ids:
                joined = [(guild_user["display_name"], guild_user["username"])]
        return joined