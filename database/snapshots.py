class SnapshotManager:
    def __init__(self, database, bot, api):
        self.database = database
        self.pool = self.database.pool
        self.bot = bot
        self.api = api

    async def get_latest_snapshot_id(self, guild):
        async with self.pool.acquire() as conn:
            snapshot_id = await conn.fetchval("""
                SELECT snapshot_id
                FROM snapshot_metadata
                WHERE guild_id = $1
                ORDER BY snapshot_id DESC
                LIMIT 1
            """, guild.id)
            return snapshot_id

    async def save_snapshot(self, guild):
        user_ids = await self.bot.user_manager.get_guild_user_ids(guild)
        async with self.pool.acquire() as conn:
            snapshot_id = await conn.fetchval("""
                INSERT INTO snapshot_metadata (guild_id)
                VALUES ($1)
                RETURNING snapshot_id
            """, guild.id)

        total_rows = await self.bot.stat_manager.get_total_playtimes(user_ids)
        game_rows = await self.bot.stat_manager.get_game_playtimes(user_ids)

        total_playtimes = [(snapshot_id, *row) for row in total_rows]
        game_playtimes = [(snapshot_id, *row) for row in game_rows]

        async with self.pool.acquire() as conn:
            await conn.executemany(f"""
                INSERT INTO total_playtime_snapshots (snapshot_id, user_id, total_playtime)
                VALUES ($1, $2, $3)
                ON CONFLICT (snapshot_id, user_id)
                DO NOTHING
            """, total_playtimes)
            await conn.executemany(f"""
                INSERT INTO game_playtime_snapshots (snapshot_id, user_id, place_id, playtime)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (snapshot_id, user_id, place_id)
                DO NOTHING
            """, game_playtimes)

    async def remove_last_snapshot(self, guild):
        snapshot_id = await self.get_latest_snapshot_id(guild)
        async with self.pool.acquire() as conn:
            await conn.execute(f"""
                DELETE FROM snapshot_metadata
                WHERE guild_id = $1
                AND snapshot_id = $2
            """, guild.id, snapshot_id)
            return True

    async def diff_last_snapshot(self, guild):
        snapshot_id = await self.get_latest_snapshot_id(guild)
        if snapshot_id is None:
            return (None, None)
        async with self.pool.acquire() as conn:
            total_rows = await conn.fetch("""
                SELECT
                    s.user_id,
                    COALESCE(g.playtime, 0)
                    + COALESCE(EXTRACT(EPOCH FROM (NOW() - cp.start_time)), 0)
                    - s.total_playtime AS total_playtime
                FROM total_playtime_snapshots s
                LEFT JOIN game_playtimes g
                    ON g.user_id = s.user_id
                LEFT JOIN currently_playing cp
                    ON cp.user_id = s.user_id
                WHERE s.snapshot_id = $1
            """, snapshot_id)

            game_rows = await conn.fetch("""
                SELECT
                    s.user_id,
                    s.place_id,
                    COALESCE(g.playtime, 0)
                    + COALESCE(EXTRACT(EPOCH FROM (NOW() - cp.start_time)), 0)
                    - s.playtime AS playtime
                FROM game_playtime_snapshots s
                LEFT JOIN game_playtimes g
                    ON g.user_id = s.user_id
                    AND g.place_id = s.place_id
                LEFT JOIN currently_playing cp
                    ON cp.user_id = s.user_id
                    AND cp.place_id = s.place_id
                WHERE s.snapshot_id = $1
            """, snapshot_id)

        return (total_rows, game_rows)