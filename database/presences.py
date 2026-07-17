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

    async def get_guild_presences(self, guild_id, presence_type):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT *
                FROM subscriptions
                WHERE guild_id = $1
            """, guild_id)
        
        user_ids = [row["user_id"] for row in rows]
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(f"""
                SELECT *
                FROM {"old_presences" if presence_type == "old" else "presences"}
                WHERE user_id = ANY($1)
            """, user_ids)
        
        if len(rows) > 0:
            presences = {
                user_ids[i]: {
                    "game_instance_id": rows[i]["game_instance_id"],
                    "place_id": rows[i]["place_id"],
                    "user_status": rows[i]["user_status"]
                }
                for i in range(len(rows))
            }
        else:
            presences = {
                user_ids[i]: {
                    "game_instance_id": None,
                    "place_id": None,
                    "user_status": 0
                }
                for i in range(len(rows))
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
            user_ids[i]: {
                "game_instance_id": rows[i]["game_instance_id"],
                "place_id": rows[i]["place_id"],
                "user_status": rows[i]["user_status"]
            }
            for i in range(len(rows))
        }

        return presences
    
    async def get_all_presences_unfiltered(self):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT *
                FROM users
            """)
        
        user_ids = [row["user_id"] for row in rows]
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(f"""
                SELECT *
                FROM presences
                WHERE user_id = ANY($1)
            """, user_ids)

        return rows