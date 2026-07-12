import time
from datetime import datetime
from storage.database import *

class StatManager:
    def __init__(self, api, user_manager):
        self.api = api
        self.user_manager = user_manager
        self.stats = load_data("stats.json")
        self.extended_stats = load_data("extended_stats.json", {"version": 1, "periods": []})

    def refresh_stats(self):
        self.stats = load_data("stats.json")

    async def fix_stats(self, user_id):
        default_stats = {
            "total_playtime": 0,
            "games_playtime": {},
            "currently_playing": {},
        }
        if str(user_id) not in self.stats:
            self.stats[str(user_id)] = {}
        for key in default_stats.keys():
            if key not in self.stats[str(user_id)]:
                self.stats[str(user_id)][key] = default_stats[key]
        save_data(self.stats, "stats.json")

    async def save_period(self):
        stats_temp = self.stats
        for user in stats_temp:
            if stats_temp[user]["currently_playing"] != {}:
                currently_playing = stats_temp[user]["currently_playing"]
                if str(currently_playing["root_place_id"]) in stats_temp[user]["games_playtime"]:
                    stats_temp[user]["games_playtime"][str(currently_playing["root_place_id"])]["playtime"] += round(time.time() - currently_playing["start"])
                else:
                    stats_temp[user]["games_playtime"][str(currently_playing["root_place_id"])] = {"playtime": round(time.time() - currently_playing["start"])}
                stats_temp[user]["currently_playing"] = {}
        self.extended_stats["periods"] += [stats_temp]
        save_data(self.extended_stats, "extended_stats.json")

    async def remove_last_period(self):
        if len(self.extended_stats) > 1:
            del self.extended_stats["periods"][-1]
            save_data(self.extended_stats, "extended_stats.json")
            return True
        else:
            return False

    async def get_playtime(self, user_id, place_id, playtime_type):
        playtime = 0
        rpid = await self.api.get_root_place_id(place_id)
        await self.fix_stats(user_id)

        if playtime_type == "both" and str(rpid) in self.stats[user_id]["games_playtime"]:
            playtime += self.stats[user_id]["games_playtime"][str(rpid)]["playtime"]
        if (
            playtime_type in ["current", "both"]
            and "root_place_id" in self.stats[user_id]["currently_playing"]
        ):
            if self.stats[user_id]["currently_playing"]["root_place_id"] == rpid:
                playtime += (round(time.time()) - self.stats[user_id]["currently_playing"]["start"])
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

    async def start_tracking_playtime(self, int_user_id, place_id, game_instance_id):
        user_id = str(int_user_id)
        await self.fix_stats(user_id)
        if self.stats[user_id]["currently_playing"] != {}:
            await self.finish_tracking_playtime(user_id)
        root_place_id = await self.api.get_root_place_id(place_id)
        self.stats[user_id]["currently_playing"] = {
            "root_place_id": root_place_id,
            "game_instance_id": game_instance_id,
            "start": round(time.time()),
        }
        save_data(self.stats, "stats.json")


    async def finish_tracking_playtime(self, int_user_id):
        user_id = str(int_user_id)
        await self.fix_stats(user_id)
        current = self.stats[user_id]["currently_playing"]
        if "start" in current:
            root_place_id = current.get("root_place_id")
            diff = round(time.time()) - current["start"]
            if str(root_place_id) not in self.stats[user_id]["games_playtime"]:
                self.stats[user_id]["games_playtime"][str(root_place_id)] = {"playtime": diff}
            else:
                self.stats[user_id]["games_playtime"][str(root_place_id)]["playtime"] += diff
            self.stats[user_id]["total_playtime"] = sum(
                [
                    playtime["playtime"]
                    for playtime in self.stats[user_id]["games_playtime"].values()
                ]
            )
            self.stats[user_id]["currently_playing"] = {}
        save_data(self.stats, "stats.json")

    async def get_data(self, stats_temp={}):
        total = 0
        playtimes = {}
        game_playtimes = {}
        if stats_temp == {}:
            stats_temp = self.stats
        for user in stats_temp:
            if stats_temp[user]["currently_playing"] != {}:
                currently_playing = stats_temp[user]["currently_playing"]
                if str(currently_playing["root_place_id"]) in stats_temp[user]["games_playtime"]:
                    stats_temp[user]["games_playtime"][str(currently_playing["root_place_id"])]["playtime"] += round(time.time() - currently_playing["start"])
                else:
                    stats_temp[user]["games_playtime"][str(currently_playing["root_place_id"])] = {"playtime": round(time.time() - currently_playing["start"])}
                stats_temp[user]["currently_playing"] = {}

            playtimes[user] = 0
            for game in stats_temp[user]["games_playtime"].keys():
                if game not in game_playtimes:
                    game_playtimes[game] = 0
                game_playtimes[game] += stats_temp[user]["games_playtime"][game]["playtime"]
                total += stats_temp[user]["games_playtime"][game]["playtime"]
                playtimes[user] += stats_temp[user]["games_playtime"][game]["playtime"]
            
        return (total, playtimes, game_playtimes)

    async def get_diff(self, old, new):
        diff = {}
        for user in new.keys():
            if user not in old:
                diff[user] = new[user]
                continue
            diff[user] = {"games_playtime": {}, "currently_playing": new[user]["currently_playing"]}
            diff[user]["total_playtime"] = new[user]["total_playtime"] - old[user]["total_playtime"]
            for game in new[user]["games_playtime"].keys():
                if not game in old[user]["games_playtime"]:
                    diff[user]["games_playtime"][game] = new[user]["games_playtime"][game]
                    continue
                diff[user]["games_playtime"][game] = {"playtime": new[user]["games_playtime"][game]["playtime"] - old[user]["games_playtime"][game]["playtime"]}
        return diff

    async def get_user_leaderboard(self, total, playtimes, game_playtimes):
        message_content = f"\n**Total Server Playtime:** {total / 3600:.2f}h"

        message_content += f"\n**Playtime for Top 10 Users:**"
        playtimes = sorted(playtimes.items(), key=lambda item: item[1], reverse=True)[:10]
        for i, (user, playtime) in enumerate(playtimes, start=1):
            message_content += f"\n[#{i}] {self.user_manager.users[user]["display_name"]} ({playtime / 3600:.2f}h)"

        message_content += f"\n\n**Playtime for Top 10 Games:**"
        game_playtimes = sorted(game_playtimes.items(), key=lambda item: item[1], reverse=True)[:10]
        for i, (game, playtime) in enumerate(game_playtimes, start=1):
            if str(game) not in self.api.cache["indexes"]:
                await self.api.cache_id(game)
            universe_id = self.api.cache["indexes"][str(game)]
            name = self.api.cache["caches"][str(universe_id)]["name"]
            message_content += f"\n[#{i}] {name}: {playtime / 3600:.2f}h"
        
        return message_content

    async def get_game_leaderboard(self, stats, place_id):
        total = 0
        playtimes = {}
        for user_id, statistics in stats.items():
            current_playtime = 0
            stored_playtime = 0
            if statistics["currently_playing"] != {}:
                if str(statistics["currently_playing"]["root_place_id"]) == str(place_id):
                    current_playtime = round(time.time() - statistics["currently_playing"]["start"])
            if str(place_id) in statistics["games_playtime"]:
                stored_playtime = statistics["games_playtime"][str(place_id)]["playtime"]
            if (current_playtime + stored_playtime) > 0:
                playtimes[str(user_id)] = (current_playtime + stored_playtime)
                total += (current_playtime + stored_playtime)

        if str(place_id) not in self.api.cache["indexes"]:
            await self.api.cache_id(place_id)
        universe_id = self.api.cache["indexes"][str(place_id)]
        name = self.api.cache["caches"][str(universe_id)]["name"]
        message_title = f"Leaderboard for {name}"
        message_content = f"\n**Total Server Playtime:** {total / 3600:.2f}h"

        message_content += f"\n**Playtime for Top 20 Users:**"
        if len(list(playtimes.keys())) == 0:
            message_content += f"\nNo one has played this game yet."
        else:
            playtimes = sorted(playtimes.items(), key=lambda item: item[1], reverse=True)[:20]
            for i, (user, playtime) in enumerate(playtimes, start=1):
                message_content += f"\n[#{i}] {self.user_manager.users[str(user)]["display_name"]} ({playtime / 3600:.2f}h)"
        
        return (message_title, message_content)

    async def get_user_stats(self, user_id):
        creation_date = datetime.now().strftime("%m-%d-%Y")
        creation_time = datetime.now().strftime("%H:%M:%S")

        total, playtimes, game_playtimes = await self.get_data({str(user_id): self.stats[str(user_id)]})
        total_server, playtimes_server, game_playtimes_server = await self.get_data()
        playtimes_server = sorted(playtimes_server.items(), key=lambda item: item[1], reverse=True)
        game_playtimes_server = sorted(game_playtimes_server.items(), key=lambda item: item[1], reverse=True)

        diff_server_week = await self.get_diff(self.extended_stats["periods"][-1], self.stats)
        diff_player_week = diff_server_week[str(user_id)]
        total_weekly, playtimes_weekly, game_playtimes_weekly = await self.get_data({str(user_id): diff_player_week})
        total_server_weekly, playtimes_server_weekly, game_playtimes_server_weekly = await self.get_data(diff_server_week)
        playtimes_server_weekly = sorted(playtimes_server_weekly.items(), key=lambda item: item[1], reverse=True)
        game_playtimes_server_weekly = sorted(game_playtimes_server_weekly.items(), key=lambda item: item[1], reverse=True)

        message_title = f"{self.user_manager.users[user_id]["display_name"]}'s usercard"
        message_content = f"Created on {creation_date} @ {creation_time} EST"

        message_content += f"\n\n**Your Playtimes:**"
        message_content += f"\nOverall Playtime: {total / 3600:.2f}h"
        message_content += f"\nWeekly Playtime: {total_weekly / 3600:.2f}h"

        message_content += f"\n\n**Your Standings:**"
        message_content += f"\nOverall Leaderboard Position: #{playtimes_server.index((str(user_id), total)) + 1}"
        message_content += f"\nWeekly Leaderboard Position: #{playtimes_server_weekly.index((str(user_id), total_weekly)) + 1}"

        message_content += f"\n\n**Your Top 5 Games Overall:**"
        game_playtimes = sorted(game_playtimes.items(), key=lambda item: item[1], reverse=True)[:5]
        for i, (game, playtime) in enumerate(game_playtimes, start=1):
            if str(game) not in self.api.cache["indexes"]:
                await self.api.cache_id(game)
            universe_id = self.api.cache["indexes"][str(game)]
            name = self.api.cache["caches"][str(universe_id)]["name"]
            message_content += f"\n[#{i}] {name}: {playtime / 3600:.2f}h"
        
        weekly_games = 0
        message_content += f"\n\n**Your Top 5 Games This Week:**"
        game_playtimes_weekly = sorted(game_playtimes_weekly.items(), key=lambda item: item[1], reverse=True)[:5]
        for i, (game, playtime) in enumerate(game_playtimes_weekly, start=1):
            if playtime == 0:
                continue
            if str(game) not in self.api.cache["indexes"]:
                await self.api.cache_id(game)
            universe_id = self.api.cache["indexes"][str(game)]
            name = self.api.cache["caches"][str(universe_id)]["name"]
            message_content += f"\n[#{i}] {name}: {playtime / 3600:.2f}h"
            weekly_games += 1
        if weekly_games == 0:
            message_content += f"\nYou haven't played any games this week."

        return (message_title, message_content)

    async def get_alltime_user_leaderboard(self):
        data = await self.get_data()
        message_title = "All-Time Playtime Leaderboard"
        message_content = await self.get_user_leaderboard(*data)
        return (message_title, message_content)

    async def get_weekly_user_leaderboard(self):
        weekly_diff = await self.get_diff(self.extended_stats["periods"][-1], self.stats)
        weekly_data = await self.get_data(weekly_diff)
        message_title = "Weekly Playtime Leaderboard"
        message_content = await self.get_user_leaderboard(*weekly_data)
        return (message_title, message_content)

    async def get_alltime_game_leaderboard(self, place_id):
        (message_title, message_content) = await self.get_game_leaderboard(self.stats, place_id)
        return (message_title, message_content)

    async def get_weekly_game_leaderboard(self, place_id):
        weekly_diff = await self.get_diff(self.extended_stats["periods"][-1], self.stats)
        (message_title, message_content) = await self.get_game_leaderboard(weekly_diff, place_id)
        return (message_title, message_content)