import time
from datetime import datetime
from storage.database import *

class StatManager:
    def __init__(self, api, user_manager):
        self.api = api
        self.user_manager = user_manager
        self.stats = load_data("stats.json")
    
    def refresh_stats(self):
        self.stats = load_data("stats.json")

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

    async def get_playtime_str(self, user_id, place_id, playtime_type):
        playtime = 0
        rpid = await self.api.get_root_place_id(place_id)
        self.fix_stats(user_id)

        if playtime_type == "both" and str(rpid) in self.stats[user_id]["games_playtime"]:
            playtime += self.stats[user_id]["games_playtime"][str(rpid)]["playtime"]
        if (
            playtime_type in ["current", "both"]
            and "root_place_id" in self.stats[user_id]["currently_playing"]
        ):
            if self.stats[user_id]["currently_playing"]["root_place_id"] == rpid:
                playtime += (round(time.time()) - self.stats[user_id]["currently_playing"]["start"])

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
        self.fix_stats(user_id)
        if self.stats[user_id]["currently_playing"] != {}:
            self.finish_tracking_playtime(user_id)
        root_place_id = await self.api.get_root_place_id(place_id)
        self.stats[user_id]["currently_playing"] = {
            "root_place_id": root_place_id,
            "game_instance_id": game_instance_id,
            "start": round(time.time()),
        }
        save_data(self.stats, "stats.json")


    def finish_tracking_playtime(self, int_user_id):
        user_id = str(int_user_id)
        self.fix_stats(user_id)
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

    def fix_stats(self, user_id):
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
    
    async def get_user_leaderboard(self, total, playtimes, game_playtimes):
        message_content = f"\n**Total Server Playtime:** {total / 3600:.2f}h"

        message_content += f"\n**Playtime for Top 10 Users:**"
        playtimes = sorted(playtimes.items(), key=lambda item: item[1], reverse=True)[:10]
        for i, (user, playtime) in enumerate(playtimes, start=1):
            message_content += f"\n[#{i}] {self.user_manager.users[user]["display_name"]} ({playtime / 3600:.2f}h)"

        message_content += f"\n\n**Playtime for Top 10 Games:**"
        game_playtimes = sorted(game_playtimes.items(), key=lambda item: item[1], reverse=True)[:10]
        for i, (game, playtime) in enumerate(game_playtimes, start=1):
            universe_id = self.api.cache["indexes"][str(game)]
            name = self.api.cache["caches"][str(universe_id)]["name"]
            message_content += f"\n[#{i}] {name}: {playtime / 3600:.2f}h"
        
        return message_content

    async def get_game_leaderboard(self, place_id):
        total = 0
        playtimes = {}
        stats_temp = self.stats
        for user_id, statistics in stats_temp.items():
            if str(place_id) in statistics["games_playtime"]:
                playtimes[str(user_id)] = statistics["games_playtime"][str(place_id)]["playtime"]
                total += statistics["games_playtime"][str(place_id)]["playtime"]

        universe_id = self.api.cache["indexes"][str(place_id)]
        name = self.api.cache["caches"][str(universe_id)]["name"]
        message_title = f"Leaderboard for {name}"
        message_content = f"\n**Total Server Playtime:** {total / 3600:.2f}h"

        message_content += f"\n**Playtime for Top 20 Users:**"
        playtimes = sorted(playtimes.items(), key=lambda item: item[1], reverse=True)[:20]
        for i, (user, playtime) in enumerate(playtimes, start=1):
            message_content += f"\n[#{i}] {self.user_manager.users[str(user)]["display_name"]} ({playtime / 3600:.2f}h)"
        
        return (message_title, message_content)

    async def get_user_stats(self, user_id):
        creation_date = datetime.now().strftime("%m-%d-%Y")
        creation_time = datetime.now().strftime("%H:%M:%S")

        total, playtimes, game_playtimes = self.get_data({str(user_id): self.stats[str(user_id)]})
        total_server, playtimes_server, game_playtimes_server = self.get_data()
        playtimes_server = sorted(playtimes_server.items(), key=lambda item: item[1], reverse=True)
        game_playtimes_server = sorted(game_playtimes_server.items(), key=lambda item: item[1], reverse=True)

        message_content = ""

        message_content += f"## [{self.user_manager.users[user_id]["display_name"]}'s usercard]"
        message_content += f"Created on {creation_date} @ {creation_time} EST"

        message_content += f"\n**Your Playtimes:**",
        message_content += f"Overall Playtime: {total / 3600:.2f}h"
        
        message_content += f"\n**Your Standings:**"
        message_content += f"Overall Leaderboard Position: #{playtimes_server.index((str(user_id), total)) + 1}"

        message_content += f"\nYour Top 5 Games Overall:"
        game_playtimes = sorted(game_playtimes.items(), key=lambda item: item[1], reverse=True)[:5]
        for i, (game, playtime) in enumerate(game_playtimes, start=1):
            universe_id = self.api.cache["indexes"][str(game)]
            name = self.api.cache["caches"][str(universe_id)]["name"]
            message_content += f"\n[#{i}] {name}: {playtime / 3600:.2f}h"

    async def get_alltime_user_leaderboard(self):
        data = await self.get_data()
        message_content = await self.get_user_leaderboard(*data)
        return message_content