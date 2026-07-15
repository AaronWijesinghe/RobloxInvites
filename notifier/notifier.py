from styling.ri_colors import *
from styling.formatting import *
from database.database import *
from notifier.send_embed import send_embed
from copy import deepcopy
import time

class Notifier:
    def __init__(self, bot):
        self.bot = bot
        self.user_presences = {}
        self.transfers = {}

    async def send_guild_updates(self, guild):
        guild_user_ids = await self.bot.api.get_guild_user_ids(guild)
        guild_presences = await self.bot.api.get_guild_presences(guild, "current")
        old_guild_presences = await self.bot.api.get_guild_presences(guild, "old")

        for i in guild_presences:
            user_id = guild_user_ids[i]

            status = guild_presences[i]["status"]
            place_id = guild_presences[i]["place_id"]
            game_instance_id = guild_presences[i]["game_instance_id"]

            if status in [0, 1]:
                if user_id in self.old_user_presences:
                    if self.old_user_presences[user_id]["status"] == 2 and user_id not in self.transfers:
                        self.transfers[user_id] = {
                            "old_place_id": self.old_user_presences[user_id]["place_id"],
                            "old_game_instance_id": self.old_user_presences[user_id]["game_instance_id"],
                            "username": self.bot.user_manager.users[user_id]["username"],
                        }
                    elif user_id in self.transfers:
                        await self.send_leave_message(user_id, self.transfers[user_id]["old_place_id"], "absolute" if status == 0 else "website")
                        await self.bot.stat_manager.finish_tracking_playtime(user_id)
                        del self.transfers[user_id]
                    elif user_id in self.bot.stat_manager.stats:
                        if self.bot.stat_manager.stats[user_id]["currently_playing"] != {}:
                            await self.bot.stat_manager.finish_tracking_playtime(user_id)
                print(f"{self.bot.user_manager.users[user_id]["display_name"]} is {'offline.' if status == 0 else 'on the Roblox website!'}")
            elif status == 2 and (game_instance_id is None or place_id is None):
                print(f"{self.bot.user_manager.users[user_id]["display_name"]} has their joins off, or you aren't following them.")
                print(f"   -> Follow them @ https://roblox.com/users/{user_id}/profile")
            elif status == 2:
                if user_id in self.old_user_presences:
                    if user_id in self.transfers:
                        if [
                            self.transfers[user_id]["old_place_id"],
                            self.transfers[user_id]["old_game_instance_id"],
                        ] == [place_id, game_instance_id]:
                            del self.transfers[user_id]
                        elif await self.bot.api.check_root_place_id(self.transfers[user_id]["old_place_id"], place_id):
                            self.bot.stat_manager.stats[user_id]["currently_playing"]["game_instance_id"] = game_instance_id
                            await self.send_invite(user_id, place_id, game_instance_id, transfer=True)
                        else:
                            await self.bot.stat_manager.start_tracking_playtime(user_id, place_id, game_instance_id)
                            await self.send_invite(user_id, place_id, game_instance_id)
                        continue

                    if self.user_presences[user_id] != self.old_user_presences[user_id]:
                        if await self.bot.api.check_root_place_id(self.old_user_presences[user_id]["place_id"], place_id):
                            self.bot.stat_manager.stats[user_id]["currently_playing"]["game_instance_id"] = (game_instance_id)
                            await self.send_invite(user_id, place_id, game_instance_id, transfer=True)
                        else:
                            await self.bot.stat_manager.start_tracking_playtime(user_id, place_id, game_instance_id)
                            await self.send_invite(user_id, place_id, game_instance_id)
                else:
                    await self.bot.stat_manager.start_tracking_playtime(user_id, place_id, game_instance_id)
                    await self.send_invite(user_id, place_id, game_instance_id)
                print(f"{self.bot.user_manager.users[user_id]["display_name"]} is in a game: {underline}roblox://experiences/start?placeId={place_id}&gameInstanceId={game_instance_id}{end}")
            elif status == 3:
                print(f"{self.bot.user_manager.users[user_id]["display_name"]} is in Roblox Studio.")

            if "delete" in self.bot.user_manager.users[user_id]:
                del self.bot.user_manager.users[user_id]
                del self.user_presences[user_id]
                if user_id in self.bot.stat_manager.stats:
                    del self.bot.stat_manager.stats[user_id]
                    await save_data(self.bot.stat_manager.stats, "stats.json")
                await save_data(self.bot.user_manager.users, "users.json")
        self.old_user_presences = deepcopy(self.user_presences)
        await save_data(self.old_user_presences, "old_user_presences.json")

    async def process_updates_gui(self, user_ids):
        new_presences = await self.bot.api.get_presences(user_ids)
        for i, user_id in enumerate(user_ids):
            self.user_presences[str(user_id)] = {
                "game_instance_id": new_presences["userPresences"][i]["gameId"],
                "place_id": new_presences["userPresences"][i]["placeId"],
                "status": new_presences["userPresences"][i]["userPresenceType"],
            }

        for user_id, presence in list(self.user_presences.items()):
            status = self.user_presences[user_id]["status"]
            place_id = self.user_presences[user_id]["place_id"]
            game_instance_id = self.user_presences[user_id]["game_instance_id"]

            if status in [0, 1]:
                if user_id in self.old_user_presences:
                    if self.old_user_presences[user_id]["status"] == 2 and user_id not in self.transfers:
                        self.transfers[user_id] = {
                            "old_place_id": self.old_user_presences[user_id]["place_id"],
                            "old_game_instance_id": self.old_user_presences[user_id]["game_instance_id"],
                            "username": self.bot.user_manager.users[user_id]["username"],
                        }
                    elif user_id in self.transfers:
                        await self.send_leave_message(user_id, self.transfers[user_id]["old_place_id"], "absolute" if status == 0 else "website")
                        await self.bot.stat_manager.finish_tracking_playtime(user_id)
                        del self.transfers[user_id]
                    elif user_id in self.bot.stat_manager.stats:
                        if self.bot.stat_manager.stats[user_id]["currently_playing"] != {}:
                            await self.bot.stat_manager.finish_tracking_playtime(user_id)
                print(f"{self.bot.user_manager.users[user_id]["display_name"]} is {'offline.' if status == 0 else 'on the Roblox website!'}")
            elif status == 2 and (game_instance_id is None or place_id is None):
                print(f"{self.bot.user_manager.users[user_id]["display_name"]} has their joins off, or you aren't following them.")
                print(f"   -> Follow them @ https://roblox.com/users/{user_id}/profile")
            elif status == 2:
                if user_id in self.old_user_presences:
                    if user_id in self.transfers:
                        if [
                            self.transfers[user_id]["old_place_id"],
                            self.transfers[user_id]["old_game_instance_id"],
                        ] == [place_id, game_instance_id]:
                            del self.transfers[user_id]
                        elif await self.bot.api.check_root_place_id(self.transfers[user_id]["old_place_id"], place_id):
                            self.bot.stat_manager.stats[user_id]["currently_playing"]["game_instance_id"] = game_instance_id
                            await self.send_invite(user_id, place_id, game_instance_id, transfer=True)
                        else:
                            await self.bot.stat_manager.start_tracking_playtime(user_id, place_id, game_instance_id)
                            await self.send_invite(user_id, place_id, game_instance_id)
                        continue

                    if self.user_presences[user_id] != self.old_user_presences[user_id]:
                        if await self.bot.api.check_root_place_id(self.old_user_presences[user_id]["place_id"], place_id):
                            self.bot.stat_manager.stats[user_id]["currently_playing"]["game_instance_id"] = (game_instance_id)
                            await self.send_invite(user_id, place_id, game_instance_id, transfer=True)
                        else:
                            await self.bot.stat_manager.start_tracking_playtime(user_id, place_id, game_instance_id)
                            await self.send_invite(user_id, place_id, game_instance_id)
                else:
                    await self.bot.stat_manager.start_tracking_playtime(user_id, place_id, game_instance_id)
                    await self.send_invite(user_id, place_id, game_instance_id)
                print(f"{self.bot.user_manager.users[user_id]["display_name"]} is in a game: {underline}roblox://experiences/start?placeId={place_id}&gameInstanceId={game_instance_id}{end}")
            elif status == 3:
                print(f"{self.bot.user_manager.users[user_id]["display_name"]} is in Roblox Studio.")

            if "delete" in self.bot.user_manager.users[user_id]:
                del self.bot.user_manager.users[user_id]
                del self.user_presences[user_id]
                if user_id in self.bot.stat_manager.stats:
                    del self.bot.stat_manager.stats[user_id]
                    await save_data(self.bot.stat_manager.stats, "stats.json")
                await save_data(self.bot.user_manager.users, "users.json")
        self.old_user_presences = deepcopy(self.user_presences)
        await save_data(self.old_user_presences, "old_user_presences.json")