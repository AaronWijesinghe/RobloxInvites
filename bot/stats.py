import time
from storage.database import *

class StatManager:
    def __init__(self, api):
        self.api = api
        self.stats = load_data("stats.json")
    
    def refresh_stats(self):
        self.stats = load_data("stats.json")

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