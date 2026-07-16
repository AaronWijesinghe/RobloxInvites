from styling.ansi import *
from styling.ri_colors import *
from styling.formatting import *
from database.database import *
from notifier.send_embed import send_embed
from copy import deepcopy

class Notifier:
    def __init__(self, bot):
        self.bot = bot
        self.transfers = {}

    async def send_guild_updates(self, guild):
        guild_presences = await self.bot.presence_manager.get_guild_presences(guild.id, "current")
        old_guild_presences = await self.bot.presence_manager.get_guild_presences(guild.id, "old")
        users = await self.bot.user_manager.get_all_users()

        for user_id in guild_presences:
            status = guild_presences[user_id]["user_status"]
            place_id = guild_presences[user_id]["place_id"]
            game_instance_id = guild_presences[user_id]["game_instance_id"]

            old_status = old_guild_presences[user_id]["user_status"]
            old_place_id = old_guild_presences[user_id]["place_id"]
            old_game_instance_id = old_guild_presences[user_id]["game_instance_id"]

            if status in [0, 1]:
                if user_id in old_guild_presences:
                    if old_status == 2 and user_id not in self.transfers:
                        await self.bot.transfer_manager.add_transfer(user_id, old_place_id, old_game_instance_id)
                    elif await self.bot.transfer_manager.check_transfer(user_id):
                        transfer = await self.bot.transfer_manager.get_transfer(user_id)
                        await self.send_leave_message(user_id, transfer["old_place_id"], "absolute" if status == 0 else "website")
                        #await self.bot.stat_manager.finish_tracking_playtime(user_id)
                        await self.bot.transfer_manager.remove_transfer(user_id)
                    #elif user_id in self.bot.stat_manager.stats:
                    #    if self.bot.stat_manager.stats[user_id]["currently_playing"] != {}:
                    #        await self.bot.stat_manager.finish_tracking_playtime(user_id)
                print(f"{users[user_id]["display_name"]} is {'offline.' if status == 0 else 'on the Roblox website!'}")
            elif status == 2 and (game_instance_id is None or place_id is None):
                print(f"{users[user_id]["display_name"]} has their joins off, or you aren't following them.")
                print(f"   -> Follow them @ https://roblox.com/users/{user_id}/profile")
            elif status == 2:
                if user_id in old_guild_presences:
                    if await self.bot.transfer_manager.check_transfer(user_id) == True:
                        transfer = await self.bot.transfer_manager.get_transfer(user_id)
                        if [transfer["old_place_id"], transfer["old_game_instance_id"]] == [place_id, game_instance_id]:
                            await self.bot.transfer_manager.remove_transfer(user_id)
                        elif await self.bot.api.check_root_place_id(transfer["old_place_id"], place_id):
                            #self.bot.stat_manager.stats[user_id]["currently_playing"]["game_instance_id"] = game_instance_id
                            await self.send_invite(user_id, place_id, game_instance_id, transfer=True)
                        else:
                            #await self.bot.stat_manager.start_tracking_playtime(user_id, place_id, game_instance_id)
                            await self.send_invite(user_id, place_id, game_instance_id)
                        continue

                    if guild_presences[user_id] != old_guild_presences[user_id]:
                        if await self.bot.api.check_root_place_id(old_guild_presences[user_id]["place_id"], place_id):
                            #self.bot.stat_manager.stats[user_id]["currently_playing"]["game_instance_id"] = (game_instance_id)
                            await self.send_invite(user_id, place_id, game_instance_id, transfer=True)
                        else:
                            #await self.bot.stat_manager.start_tracking_playtime(user_id, place_id, game_instance_id)
                            await self.send_invite(user_id, place_id, game_instance_id)
                else:
                    #await self.bot.stat_manager.start_tracking_playtime(user_id, place_id, game_instance_id)
                    await self.send_invite(user_id, place_id, game_instance_id)
                print(f"{users[user_id]["display_name"]} is in a game: {underline}roblox://experiences/start?placeId={place_id}&gameInstanceId={game_instance_id}{end}")
            elif status == 3:
                print(f"{users[user_id]["display_name"]} is in Roblox Studio.")

        # this is a dry run, data won't be modified! also, old presence data will now be written to outside of the Notifier class.
        #self.old_user_presences = deepcopy(self.user_presences)
        #await save_data(self.old_user_presences, "old_user_presences.json")
    
    async def send_invite(self, arg_1, arg_2, arg_3, arg_4=None):
        await send_embed(self.bot, "example join message", f"placeholder message, see args below:\n{arg_1}\n{arg_2}\n{arg_3}\n{arg_4}", green, 1494129250343583898)

    async def send_leave_message(self, arg_1, arg_2, arg_3):
        await send_embed(self.bot, "example leave message", f"placeholder message, see args below:\n{arg_1}\n{arg_2}\n{arg_3}", red, 1494129250343583898)