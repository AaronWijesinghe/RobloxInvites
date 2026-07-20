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
                    tp.user_id,
                    tp.total_playtime +
                    COALESCE(
                        EXTRACT(EPOCH FROM (NOW() - cp.start_time)),
                        0
                    ) AS total_playtime
                FROM total_playtimes tp
                LEFT JOIN currently_playing cp
                    ON tp.user_id = cp.user_id
                WHERE tp.user_id = $1
                ORDER BY tp.total_playtime
            """, user_id)
            if total_playtime is None:
                return 0
            return total_playtime

    async def get_total_game_playtime(self, place_id):
        async with self.pool.acquire() as conn:
            playtime = await conn.fetchval("""
                SELECT playtime
                FROM game_playtimes
                WHERE place_id = $1
            """, place_id)
            if playtime is None:
                return 0
            return playtime

    async def get_game_playtime(self, user_id, place_id):
        async with self.pool.acquire() as conn:
            playtime = await conn.fetchval("""
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
                WHERE gp.user_id = $1
                AND gp.place_id = $2
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

    async def save_snapshot(self, guild):
        user_ids = await self.user_manager.get_guild_user_ids(guild)
        async with self.pool.acquire() as conn:
            snapshot_id = await conn.fetchval("""
                INSERT INTO snapshot_metadata (guild_id)
                VALUES ($1)
                RETURNING snapshot_id
            """, guild.id)

        total_rows = await self.get_total_playtimes(user_ids)
        game_rows = await self.get_game_playtimes(user_ids)

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
        async with self.pool.acquire() as conn:
            await conn.execute(f"""
                DELETE FROM snapshot_metadata
                WHERE guild_id = $1
                AND snapshot_id = (
                    SELECT snapshot_id
                    FROM snapshot_metadata
                    WHERE guild_id = $1
                    ORDER BY snapshot_id DESC
                    LIMIT 1
                );
            """, guild.id)
            return True

    async def diff_last_snapshot(self, guild):
        async with self.pool.acquire() as conn:
            snapshot_id = await conn.fetchval("""
                SELECT snapshot_id
                FROM snapshot_metadata
                WHERE guild_id = $1
                ORDER BY snapshot_id DESC
                LIMIT 1
            """, guild.id)

            if snapshot_id is None:
                return (None, None)

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

    async def get_snapshot_total_playtimes(self, snapshot_id):
        async with self.pool.acquire() as conn:
            total_rows = await conn.fetch("""
                SELECT *
                FROM total_playtime_snapshots
                WHERE snapshot_id = $1
            """, snapshot_id)
            return total_rows
    
    async def get_snapshot_game_playtimes(self, snapshot_id):
        async with self.pool.acquire() as conn:
            game_rows = await conn.fetch("""
                SELECT *
                FROM game_playtime_snapshots
                WHERE snapshot_id = $1
            """, snapshot_id)
            return game_rows

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

    async def get_user_leaderboard(self, playtimes, game_playtimes, total):
        message_content = f"\n**Total Server Playtime:** {total / 3600:.2f}h"

        message_content += f"\n**Playtime for Top 10 Users:**"
        playtimes = sorted(playtimes.items(), key=lambda item: item[1], reverse=True)[:10]
        for i, (user, playtime) in enumerate(playtimes, start=1):
            display_name = await self.user_manager.get_display_name(user)
            message_content += f"\n[#{i}] {display_name} ({playtime / 3600:.2f}h)"

        message_content += f"\n\n**Playtime for Top 10 Games:**"
        game_playtimes = sorted(game_playtimes.items(), key=lambda item: item[1], reverse=True)[:10]

        if total == 0:
            message_content += f"\nNo one has played yet."
        else:
            for i, (place_id, playtime) in enumerate(game_playtimes, start=1):
                await self.api.cache_id(place_id)
                name = await self.api.get_game_name(place_id)
                message_content += f"\n[#{i}] {name}: {playtime / 3600:.2f}h"
        
        return message_content

    async def get_game_leaderboard(self, root_place_id, rows):
        playtimes = [(row["user_id"], row["playtime"]) for row in rows if row["place_id"] == root_place_id]
        total = sum([playtime[1] for playtime in playtimes])

        await self.api.cache_id(root_place_id)
        name = await self.api.get_game_name(root_place_id)
        message_title = f"Leaderboard for {name}"
        message_content = f"\n**Total Server Playtime:** {total / 3600:.2f}h"

        message_content += f"\n**Playtime for Top 20 Users:**"
        if total == 0:
            message_content += f"\nNo one has played this game yet."
        else:
            playtimes = sorted(playtimes, key=lambda item: item[1], reverse=True)[:20]
            for i, (user, playtime) in enumerate(playtimes, start=1):
                display_name = await self.user_manager.get_display_name(user)
                message_content += f"\n[#{i}] {display_name} ({playtime / 3600:.2f}h)"
        
        return (message_title, message_content)

    async def get_user_stats(self, guild, user_id):
        creation_date = datetime.now().strftime("%m-%d-%Y")
        creation_time = datetime.now().strftime("%H:%M:%S")
        guild_user_ids = await self.user_manager.get_guild_user_ids(guild)

        async with self.pool.acquire() as conn:
            snapshot_id = await conn.fetchval("""
                SELECT snapshot_id
                FROM snapshot_metadata
                WHERE guild_id = $1
                ORDER BY snapshot_id DESC
                LIMIT 1
            """, guild.id)

            leaderboard_spot = await conn.fetchval("""
                SELECT rank
                FROM (
                    SELECT
                        user_id,
                        total_playtime,
                        RANK() OVER (ORDER BY total_playtime DESC) AS rank
                    FROM total_playtimes
                    WHERE user_id = ANY($1)
                )
                WHERE user_id = $2
            """, guild_user_ids, user_id)

            game_playtimes = await conn.fetch("""
                SELECT
                    user_id,
                    place_id,
                    playtime,
                    RANK() OVER (ORDER BY playtime DESC) AS rank
                FROM game_playtimes
                WHERE user_id = $1                           
            """, user_id)

            if snapshot_id != None:
                ls_leaderboard_spot = await conn.fetchval("""
                    SELECT rank
                    FROM (
                        SELECT
                            user_id,
                            total_playtime,
                            RANK() OVER (ORDER BY total_playtime DESC) AS rank
                        FROM (
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
                            AND s.user_id = ANY($2)
                        ) playtimes
                    ) ranked
                    WHERE user_id = $3
                """, snapshot_id, guild_user_ids, user_id)

                ls_game_playtimes = await conn.fetch("""
                    SELECT
                        user_id,
                        place_id,
                        playtime,
                        RANK() OVER (ORDER BY playtime DESC) AS rank
                    FROM (
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
                        AND s.user_id = $2
                    ) games_ranked
                """, snapshot_id, user_id)

        total = await self.get_total_playtime(user_id)

        display_name = await self.user_manager.get_display_name(user_id)
        username = await self.user_manager.get_username(user_id)

        message_title = f"{display_name}'s usercard"
        message_content = f"Created on {creation_date} @ {creation_time} EST"

        message_content += f"\n\n**Your Playtimes:**"
        message_content += f"\nOverall Playtime: {total / 3600:.2f}h"

        message_content += f"\n\n**Your Standings:**"
        message_content += f"\nOverall Leaderboard Position: #{leaderboard_spot}"
        if snapshot_id != None:
            message_content += f"\nSince-Last-Snapshot Leaderboard Position: #{ls_leaderboard_spot}"

        message_content += f"\n\n**Your Top 5 Games Overall:**"
        for game in game_playtimes[:5]:
            await self.api.cache_id(game["place_id"])
            name = await self.api.get_game_name(game["place_id"])
            message_content += f"\n[#{game["rank"]}] {name}: {game["playtime"] / 3600:.2f}h"

        if snapshot_id != None:
            message_content += f"\n\n**Your Top 5 Games since Last Snapshot:**"
            for game in ls_game_playtimes[:5]:
                await self.api.cache_id(game["place_id"])
                name = await self.api.get_game_name(game["place_id"])
                message_content += f"\n[#{game["rank"]}] {name}: {game["playtime"] / 3600:.2f}h"

        return (message_title, message_content)

    async def get_alltime_user_leaderboard(self, guild):
        user_ids = await self.user_manager.get_guild_user_ids(guild)
        game_rows = await self.get_game_playtimes(user_ids)
        (playtimes, game_playtimes, total) = await self.get_playtime_data_all(game_rows)

        message_title = "All-Time Playtime Leaderboard"
        message_content = await self.get_user_leaderboard(playtimes, game_playtimes, total)

        return (message_title, message_content)

    async def get_ls_user_leaderboard(self, guild):
        total_rows, game_rows = await self.diff_last_snapshot(guild)

        if (total_rows, game_rows) == (None, None):
            message_title = "Error"
            message_content = "There are no snapshots saved."
        else:
            (playtimes, game_playtimes, total) = await self.get_playtime_data_all(game_rows)
            message_title = "Playtime Leaderboard since Last Snapshot"
            message_content = await self.get_user_leaderboard(playtimes, game_playtimes, total)

        return (message_title, message_content)

    async def get_alltime_game_leaderboard(self, guild, root_place_id):
        user_ids = await self.user_manager.get_guild_user_ids(guild)
        game_rows = await self.get_game_playtimes(user_ids, root_place_id)
        message_title, message_content = await self.get_game_leaderboard(root_place_id, game_rows)

        return (message_title, message_content)

    async def get_ls_game_leaderboard(self, guild, root_place_id):
        total_rows, game_rows = await self.diff_last_snapshot(guild)
        if (total_rows, game_rows) == (None, None):
            message_title = "Error"
            message_content = "There are no snapshots saved."
        else:
            message_title, message_content = await self.get_game_leaderboard(root_place_id, game_rows)
            message_title = f"{message_title} since Last Snapshot"

        return (message_title, message_content)