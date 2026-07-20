from datetime import datetime

class StatManager:
    def __init__(self, database, api, user_manager):
        self.database = database
        self.pool = self.database.pool
        self.api = api
        self.user_manager = user_manager
        
    async def check_currently_playing(self, user_id):
        async with self.pool.acquire() as conn:
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1
                    FROM currently_playing
                    WHERE user_id = $1
                )
            """, user_id)
            return exists

    async def check_if_game_played(self, user_id, place_id):
        async with self.pool.acquire() as conn:
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1
                    FROM game_playtimes
                    WHERE user_id = $1
                    AND place_id = $2
                )
            """, user_id, place_id)
            return exists

    async def get_current_place_id(self, user_id):
        async with self.pool.acquire() as conn:
            place_id = await conn.fetchval("""
                SELECT place_id
                FROM currently_playing
                WHERE user_id = $1
            """, user_id)
            if place_id is None:
                return 0
            return place_id

    async def get_total_playtime(self, user_id):
        async with self.pool.acquire() as conn:
            total_playtime = await conn.fetchval("""
                SELECT
                    tp.total_playtime +
                    COALESCE(
                        EXTRACT(EPOCH FROM (NOW() - cp.start_time)),
                        0
                    ) AS total_playtime
                FROM total_playtimes tp
                LEFT JOIN currently_playing cp
                    ON tp.user_id = cp.user_id
                WHERE tp.user_id = $1
            """, user_id)
            if total_playtime is None:
                return 0
            return round(total_playtime)

    async def get_total_game_playtime(self, place_id):
        async with self.pool.acquire() as conn:
            playtime = await conn.fetchval("""
                SELECT playtime
                FROM game_playtimes
                WHERE place_id = $1
            """, place_id)
            if playtime is None:
                return 0
            return round(playtime)

    async def get_game_playtime(self, user_id, place_id):
        async with self.pool.acquire() as conn:
            playtime = await conn.fetchval("""
                SELECT
                    gp.playtime +
                    COALESCE(
                        EXTRACT(EPOCH FROM (NOW() - cp.start_time)),
                        0
                    ) AS playtime
                FROM game_playtimes gp
                LEFT JOIN currently_playing cp
                    ON gp.user_id = cp.user_id
                    AND gp.place_id = cp.place_id
                WHERE gp.user_id = $1
                AND gp.place_id = $2
            """, user_id, place_id)
            if playtime is None:
                return 0
            return round(playtime)

    async def get_current_playtime(self, user_id):
        async with self.pool.acquire() as conn:
            start_time = await conn.fetchval("""
                SELECT start_time
                FROM currently_playing
                WHERE user_id = $1
            """, user_id)
            if start_time is None:
                return 0
            diff = datetime.now() - start_time
            current_playtime = round(diff.total_seconds())
            return round(current_playtime)

    async def get_total_playtimes(self, user_ids):
        async with self.pool.acquire() as conn:
            total_rows = await conn.fetch("""
                SELECT
                    tp.user_id,
                    tp.total_playtime +
                    COALESCE(
                        EXTRACT(EPOCH FROM (NOW() - cp.start_time)),
                        0
                    ) AS total_playtime
                FROM total_playtimes tp
                LEFT JOIN currently_playing cp
                    ON tp.user_id = cp.user_id
                WHERE tp.user_id = ANY($1)
                ORDER BY tp.total_playtime
            """, user_ids)
            return total_rows

    async def get_game_playtimes(self, user_ids, place_id=None):
        async with self.pool.acquire() as conn:
            if place_id is None:
                game_rows = await conn.fetch("""
                    SELECT
                        gp.user_id,
                        gp.place_id,
                        gp.playtime +
                        COALESCE(
                            EXTRACT(EPOCH FROM (NOW() - cp.start_time)),
                            0
                        ) AS playtime
                    FROM game_playtimes gp
                    LEFT JOIN currently_playing cp
                        ON gp.user_id = cp.user_id
                        AND gp.place_id = cp.place_id
                    WHERE gp.user_id = ANY($1)
                """, user_ids)
            else:
                game_rows = await conn.fetch("""
                    SELECT
                        gp.user_id,
                        gp.place_id,
                        gp.playtime +
                        COALESCE(
                            EXTRACT(EPOCH FROM (NOW() - cp.start_time)),
                            0
                        ) AS playtime
                    FROM game_playtimes gp
                    LEFT JOIN currently_playing cp
                        ON gp.user_id = cp.user_id
                        AND gp.place_id = cp.place_id
                    WHERE gp.user_id = ANY($1)
                    AND gp.place_id = $2
                """, user_ids, place_id)
            return game_rows

    async def get_current_playtimes(self, user_ids):
        async with self.pool.acquire() as conn:
            current_rows = await conn.fetch("""
                SELECT *
                FROM currently_playing
                WHERE user_id = ANY($1)
            """, user_ids)
            return current_rows

    async def update_game_playtime(self, user_id, place_id, playtime):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO game_playtimes (user_id, place_id, playtime)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id, place_id)
                DO UPDATE SET
                    playtime = game_playtimes.playtime + EXCLUDED.playtime
            """, user_id, place_id, playtime)

    async def update_total_playtime(self, user_id):
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT playtime
                FROM game_playtimes
                WHERE user_id = $1
            """, user_id)
            total_playtime = sum(row["playtime"] for row in rows)

            await conn.execute("""
                INSERT INTO total_playtimes (user_id, total_playtime)
                VALUES ($1, $2)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    total_playtime = EXCLUDED.total_playtime
            """, user_id, total_playtime)

    async def set_currently_playing(self, user_id, place_id):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO currently_playing (user_id, place_id)
                VALUES ($1, $2)
            """, user_id, place_id)

    async def remove_currently_playing(self, user_id):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                DELETE FROM currently_playing
                WHERE user_id = $1
            """, user_id)

    async def get_playtime_str(self, user_id, place_id, playtime_type):
        playtime = 0
        root_place_id = await self.api.get_root_place_id(place_id)

        if playtime_type == "both":
            playtime += await self.get_game_playtime(user_id, root_place_id)
        if playtime_type in ["current", "both"]:
            playtime += await self.get_current_playtime(user_id)

        hours = round(playtime // 3600)
        minutes = round((playtime % 3600) // 60)
        seconds = playtime % 60
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    async def start_tracking_playtime(self, user_id, place_id):
        if await self.check_currently_playing(user_id):
            await self.finish_tracking_playtime(user_id)
        root_place_id = await self.api.get_root_place_id(place_id)
        await self.set_currently_playing(user_id, root_place_id)

    async def finish_tracking_playtime(self, user_id):
        if await self.check_currently_playing(user_id):
            current = await self.get_current_playtime(user_id)
            root_place_id = await self.get_current_place_id(user_id)
            await self.update_game_playtime(user_id, root_place_id, current)
            await self.update_total_playtime(user_id)
            await self.remove_currently_playing(user_id)

    async def get_playtime_data_all(self, game_rows):
        game_playtimes = {}
        playtimes = {}
        for row in game_rows:
            place_id = row["place_id"]
            user_id = row["user_id"]

            if place_id in game_playtimes:
                game_playtimes[place_id] += row["playtime"]
            else:
                game_playtimes[place_id] = row["playtime"]

            if user_id in playtimes:
                playtimes[user_id] += row["playtime"]
            else:
                playtimes[user_id] = row["playtime"]
        total = sum([row["playtime"] for row in game_rows])

        return (playtimes, game_playtimes, total)