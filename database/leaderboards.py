from datetime import datetime

class LeaderboardManager:
    def __init__(self, database, bot, api):
        self.database = database
        self.pool = self.database.pool
        self.bot = bot
        self.api = api

    async def get_leaderboard_position(self, guild, user_id):
        guild_user_ids = await self.bot.user_manager.get_guild_user_ids(guild)
        async with self.pool.acquire() as conn:
            leaderboard_spot = await conn.fetchval("""
                SELECT rank
                FROM (
                    SELECT
                        user_id,
                        total_playtime,
                        RANK() OVER (ORDER BY total_playtime DESC) AS rank
                    FROM (
                        SELECT
                            t.user_id,
                            COALESCE(t.total_playtime, 0)
                            + COALESCE(EXTRACT(EPOCH FROM (NOW() - cp.start_time)), 0) AS total_playtime
                        FROM total_playtimes t
                        LEFT JOIN currently_playing cp
                            ON cp.user_id = t.user_id
                        WHERE t.user_id = ANY($1)
                    ) playtimes
                ) ranked
                WHERE user_id = $2
            """, guild_user_ids, user_id)
            return leaderboard_spot

    async def get_ls_leaderboard_position(self, guild, user_id):
        snapshot_id = await self.bot.snapshot_manager.get_latest_snapshot_id(guild)
        async with self.pool.acquire() as conn:
            ls_leaderboard_spot = await conn.fetchval("""
                SELECT RANK() OVER (ORDER BY total_playtime DESC) AS rank
                FROM (
                    SELECT
                        s.user_id,
                        COALESCE(t.total_playtime, 0)
                        + COALESCE(EXTRACT(EPOCH FROM (NOW() - cp.start_time)), 0)
                        - s.total_playtime AS total_playtime
                    FROM total_playtime_snapshots s
                    LEFT JOIN total_playtimes t
                        ON t.user_id = s.user_id
                    LEFT JOIN currently_playing cp
                        ON cp.user_id = s.user_id
                    WHERE s.snapshot_id = $1
                ) playtimes
                WHERE user_id = $2
            """, snapshot_id, user_id)
            return ls_leaderboard_spot

    async def get_total_playtimes_ranked(self, guild):
        guild_user_ids = await self.bot.user_manager.get_guild_user_ids(guild)
        async with self.pool.acquire() as conn:
            total_playtimes_ranked = await conn.fetch("""
                SELECT
                    user_id,
                    total_playtime,
                    RANK() OVER (ORDER BY total_playtime DESC) AS rank
                FROM (
                    SELECT
                        t.user_id,
                        COALESCE(t.total_playtime, 0)
                        + COALESCE(EXTRACT(EPOCH FROM (NOW() - cp.start_time)), 0) AS total_playtime
                    FROM total_playtimes t
                    LEFT JOIN currently_playing cp
                        ON cp.user_id = t.user_id
                    WHERE t.user_id = ANY($1)
                ) playtimes
            """, guild_user_ids)
            return total_playtimes_ranked

    async def get_ls_total_playtimes_ranked(self, guild):
        snapshot_id = await self.bot.snapshot_manager.get_latest_snapshot_id(guild)
        guild_user_ids = await self.bot.user_manager.get_guild_user_ids(guild)
        async with self.pool.acquire() as conn:
            total_playtimes_ranked = await conn.fetch("""
                SELECT
                    user_id,
                    total_playtime,
                    RANK() OVER (ORDER BY total_playtime DESC) AS rank
                FROM (
                    SELECT
                        s.user_id,
                        COALESCE(s.total_playtime, 0)
                        + COALESCE(EXTRACT(EPOCH FROM (NOW() - cp.start_time)), 0) AS total_playtime
                    FROM total_playtime_snapshots s
                    LEFT JOIN currently_playing cp
                        ON cp.user_id = s.user_id
                    WHERE s.snapshot_id = $1
                    AND s.user_id = ANY($2)
                ) playtimes
            """, snapshot_id, guild_user_ids)
            return total_playtimes_ranked

    async def get_game_playtimes_ranked(self, user_id):
        async with self.pool.acquire() as conn:
            game_playtimes_ranked = await conn.fetch("""
                SELECT
                    user_id,
                    place_id,
                    playtime,
                    RANK() OVER (ORDER BY playtime DESC) AS rank
                FROM (
                    SELECT
                        g.user_id,
                        g.place_id,
                        COALESCE(g.playtime, 0)
                        + COALESCE(EXTRACT(EPOCH FROM (NOW() - cp.start_time)), 0) AS playtime
                    FROM game_playtimes g
                    LEFT JOIN currently_playing cp
                        ON cp.user_id = g.user_id
                        AND cp.place_id = g.place_id
                    WHERE g.user_id = $1
                ) games_ranked
            """, user_id)
            return game_playtimes_ranked

    async def get_ls_game_playtimes_ranked(self, guild, user_id):
        snapshot_id = await self.bot.snapshot_manager.get_latest_snapshot_id(guild)
        async with self.pool.acquire() as conn:
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
            return ls_game_playtimes

    async def get_agg_game_playtimes_ranked(self, guild):
        guild_user_ids = await self.bot.user_manager.get_guild_user_ids(guild)
        async with self.pool.acquire() as conn:
            game_playtimes_ranked = await conn.fetch("""
                SELECT
                    place_id,
                    playtime,
                    RANK() OVER (ORDER BY playtime DESC) AS rank
                FROM (
                    SELECT
                        g.place_id,
                        SUM(
                            COALESCE(g.playtime, 0)
                            + COALESCE(EXTRACT(EPOCH FROM (NOW() - cp.start_time)), 0)
                        ) AS playtime
                    FROM game_playtimes g
                    LEFT JOIN currently_playing cp
                        ON cp.user_id = g.user_id
                        AND cp.place_id = g.place_id
                    WHERE g.user_id = ANY($1)
                    GROUP BY g.place_id
                ) games_ranked
            """, guild_user_ids)
            return game_playtimes_ranked

    async def get_agg_ls_game_playtimes_ranked(self, guild):
        snapshot_id = await self.bot.snapshot_manager.get_latest_snapshot_id(guild)
        async with self.pool.acquire() as conn:
            game_playtimes_ranked = await conn.fetch("""
                SELECT
                    place_id,
                    playtime,
                    RANK() OVER (ORDER BY playtime DESC) AS rank
                FROM (
                    SELECT
                        s.place_id,
                        SUM(
                            COALESCE(g.playtime, 0)
                            + COALESCE(EXTRACT(EPOCH FROM (NOW() - cp.start_time)), 0)
                            - s.playtime
                        ) AS playtime
                    FROM game_playtime_snapshots s
                    LEFT JOIN game_playtimes g
                        ON g.user_id = s.user_id
                        AND g.place_id = s.place_id
                    LEFT JOIN currently_playing cp
                        ON cp.user_id = s.user_id
                        AND cp.place_id = s.place_id
                    WHERE s.snapshot_id = $1
                    GROUP BY s.place_id
                ) games_ranked
            """, snapshot_id)
            return game_playtimes_ranked

    async def get_user_leaderboard(self, total_playtimes, agg_game_playtimes):
        total = sum([playtime["total_playtime"] for playtime in total_playtimes])

        message_content = f"\n**Total Server Playtime:** {total / 3600:.2f}h"
        message_content += f"\n**Playtime for Top 10 Users:**"
        for playtime in total_playtimes[:10]:
            display_name = await self.bot.user_manager.get_display_name(playtime["user_id"])
            message_content += f"\n[#{playtime["rank"]}] {display_name} ({playtime["total_playtime"] / 3600:.2f}h)"

        message_content += f"\n\n**Playtime for Top 10 Games:**"
        if total == 0:
            message_content += f"\nNo one has played yet."
        else:
            for game in agg_game_playtimes[:10]:
                await self.api.cache_id(game["place_id"])
                name = await self.api.get_game_name(game["place_id"])
                message_content += f"\n[#{game["rank"]}] {name}: {game["playtime"] / 3600:.2f}h"
        
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
                display_name = await self.bot.user_manager.get_display_name(user)
                message_content += f"\n[#{i}] {display_name} ({playtime / 3600:.2f}h)"
        
        return (message_title, message_content)

    async def get_user_stats(self, guild, user_id):
        creation_date = datetime.now().strftime("%m-%d-%Y")
        creation_time = datetime.now().strftime("%H:%M:%S")

        leaderboard_spot = await self.get_leaderboard_position(guild, user_id)
        game_playtimes = await self.get_game_playtimes_ranked(user_id)

        snapshot_id = await self.bot.snapshot_manager.get_latest_snapshot_id(guild)
        if snapshot_id != None:
            ls_leaderboard_spot = await self.get_ls_leaderboard_position(guild, user_id)
            ls_game_playtimes = await self.get_ls_game_playtimes_ranked(guild, user_id)

        total = await self.bot.stat_manager.get_total_playtime(user_id)
        display_name = await self.bot.user_manager.get_display_name(user_id)
        username = await self.bot.user_manager.get_username(user_id)

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
        total_playtimes = await self.get_total_playtimes_ranked(guild)
        agg_game_playtimes = await self.get_agg_game_playtimes_ranked(guild)

        message_title = "All-Time Playtime Leaderboard"
        message_content = await self.get_user_leaderboard(total_playtimes, agg_game_playtimes)

        return (message_title, message_content)

    async def get_ls_user_leaderboard(self, guild):
        try:
            ls_total_playtimes = await self.get_ls_total_playtimes_ranked(guild)
            ls_agg_game_playtimes = await self.get_agg_ls_game_playtimes_ranked(guild)

            if (ls_total_playtimes, ls_agg_game_playtimes) == ([], []):
                message_title = "Error"
                message_content = "There are no snapshots saved."
            else:
                message_title = "Playtime Leaderboard since Last Snapshot"
                message_content = await self.get_user_leaderboard(ls_total_playtimes, ls_agg_game_playtimes)

            return (message_title, message_content)
        except:
            import traceback
            traceback.print_exc()

    async def get_alltime_game_leaderboard(self, guild, root_place_id):
        user_ids = await self.bot.user_manager.get_guild_user_ids(guild)
        game_rows = await self.bot.stat_manager.get_game_playtimes(user_ids, root_place_id)
        message_title, message_content = await self.get_game_leaderboard(root_place_id, game_rows)

        return (message_title, message_content)

    async def get_ls_game_leaderboard(self, guild, root_place_id):
        total_rows, game_rows = await self.bot.snapshot_manager.diff_last_snapshot(guild)
        if (total_rows, game_rows) == (None, None):
            message_title = "Error"
            message_content = "There are no snapshots saved."
        else:
            message_title, message_content = await self.get_game_leaderboard(root_place_id, game_rows)
            message_title = f"{message_title} since Last Snapshot"

        return (message_title, message_content)