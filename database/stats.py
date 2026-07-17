from copy import deepcopy
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

    async def get_game_playtime(self, user_id, place_id):
        async with self.pool.acquire() as conn:
            playtime = await conn.fetchval("""
                SELECT playtime
                FROM game_playtimes
                WHERE user_id = $1
                AND place_id = $2
            """, user_id, place_id)
            if playtime is None:
                return 0
            return playtime

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
            return current_playtime

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
                SELECT total_playtime
                FROM total_playtimes
                WHERE user_id = $1
            """, user_id)
            if total_playtime is None:
                return 0
            return total_playtime

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

    async def get_playtime(self, user_id, place_id, playtime_type):
        playtime = 0
        root_place_id = await self.api.get_root_place_id(place_id)

        if playtime_type == "both":
            playtime += await self.get_game_playtime(user_id, root_place_id)
        if playtime_type in ["current", "both"]:
            playtime += await self.get_current_playtime(user_id)
        return playtime

    async def get_playtime_str(self, user_id, place_id, playtime_type):
        playtime = await self.get_playtime(user_id, place_id, playtime_type)

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

    async def get_playtime_data_game(self, guild, root_place_id):
        async with self.pool.acquire() as conn:
            user_ids = await self.user_manager.get_guild_user_ids(guild)
            rows = await conn.fetch("""
                SELECT *
                FROM game_playtimes
                WHERE user_id = ANY($1)
                AND place_id = $2
            """, user_ids, root_place_id)

        game_playtimes = [(row["user_id"], row["playtime"]) for row in rows]
        total = sum([playtime[1] for playtime in game_playtimes])

        return (game_playtimes, total)

    async def get_playtime_data_all(self, guild):
        user_ids = await self.user_manager.get_guild_user_ids(guild)
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT *
                FROM game_playtimes
                WHERE user_id = ANY($1)
            """, user_ids)

        game_playtimes = {}
        playtimes = {row["user_id"]: row["playtime"] for row in rows}
        for row in rows:
            place_id = row["place_id"]
            if place_id in game_playtimes:
                game_playtimes[place_id] += row["playtime"]
            else:
                game_playtimes[place_id] = row["playtime"]
        total = sum([row["playtime"] for row in rows])

        return (playtimes, game_playtimes, total)

    async def get_user_leaderboard(self, guild):
        playtimes, game_playtimes, total = await self.get_playtime_data_all(guild)
        message_content = f"\n**Total Server Playtime:** {total / 3600:.2f}h"

        print(playtimes)
        print(list(playtimes.items()))
        message_title = "All-Time Playtime Leaderboard"
        message_content += f"\n**Playtime for Top 10 Users:**"
        playtimes = sorted(playtimes.items(), key=lambda item: item[1], reverse=True)[:10]
        for i, (user, playtime) in enumerate(playtimes, start=1):
            display_name = await self.user_manager.get_display_name(user)
            message_content += f"\n[#{i}] {display_name} ({playtime / 3600:.2f}h)"

        message_content += f"\n\n**Playtime for Top 10 Games:**"
        game_playtimes = sorted(game_playtimes.items(), key=lambda item: item[1], reverse=True)[:10]

        for i, (place_id, playtime) in enumerate(game_playtimes, start=1):
            await self.api.cache_id(place_id)
            name = await self.api.get_game_name(place_id)
            message_content += f"\n[#{i}] {name}: {playtime / 3600:.2f}h"
        
        return (message_title, message_content)


    async def get_game_leaderboard(self, guild, root_place_id):
        playtimes, total = await self.get_playtime_data_game(guild, root_place_id)
        await self.api.cache_id(root_place_id)
        name = await self.api.get_game_name(root_place_id)
        message_title = f"Leaderboard for {name}"
        message_content = f"\n**Total Server Playtime:** {total / 3600:.2f}h"

        message_content += f"\n**Playtime for Top 20 Users:**"
        if len(playtimes) == 0:
            message_content += f"\nNo one has played this game yet."
        else:
            playtimes = sorted(playtimes, key=lambda item: item[1], reverse=True)[:20]
            for i, (user, playtime) in enumerate(playtimes, start=1):
                print("3")
                display_name = await self.user_manager.get_display_name(user)
                message_content += f"\n[#{i}] {display_name} ({playtime / 3600:.2f}h)"
        
        return (message_title, message_content)