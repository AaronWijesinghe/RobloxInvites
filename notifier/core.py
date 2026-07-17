from styling.ansi import *
from styling.ri_colors import *
from styling.formatting import *
from database.database import *
from notifier.send_embed import send_embed
from copy import deepcopy

class TrackerCore:
    def __init__(self, bot):
        self.bot = bot
        self.transfers = {}

    async def send_guild_updates(self, guild):
        guild_presences = await self.bot.presence_manager.get_guild_presences(guild.id, "current")
        old_guild_presences = await self.bot.presence_manager.get_guild_presences(guild.id, "old")

        for user_id in guild_presences:
            status = guild_presences[user_id]["user_status"]
            place_id = guild_presences[user_id]["place_id"]
            game_instance_id = guild_presences[user_id]["game_instance_id"]

            if user_id in old_guild_presences:
                old_status = old_guild_presences[user_id]["user_status"]
                old_place_id = old_guild_presences[user_id]["place_id"]
                old_game_instance_id = old_guild_presences[user_id]["game_instance_id"]

            if status in [0, 1]:
                if user_id in old_guild_presences:
                    #if old_status == 2 and user_id not in self.transfers:
                        #await self.bot.transfer_manager.add_transfer(user_id, old_place_id, old_game_instance_id)
                    #elif await self.bot.transfer_manager.check_transfer(user_id):
                    if await self.bot.transfer_manager.check_transfer(user_id):
                        transfer = await self.bot.transfer_manager.get_transfer(user_id)
                        await self.send_leave_message(guild, user_id, transfer["old_place_id"], "absolute" if status == 0 else "website")
                        #await self.bot.stat_manager.finish_tracking_playtime(user_id)
                    #    await self.bot.transfer_manager.remove_transfer(user_id)
                    #elif user_id in self.bot.stat_manager.stats:
                    #    if self.bot.stat_manager.stats[user_id]["currently_playing"] != {}:
                    #        await self.bot.stat_manager.finish_tracking_playtime(user_id)
            elif status == 2:
                if user_id in old_guild_presences:
                    if await self.bot.transfer_manager.check_transfer(user_id) == True:
                        transfer = await self.bot.transfer_manager.get_transfer(user_id)
                        #if [transfer["old_place_id"], transfer["old_game_instance_id"]] == [place_id, game_instance_id]:
                        #    await self.bot.transfer_manager.remove_transfer(user_id)
                        #elif await self.bot.api.check_root_place_id(transfer["old_place_id"], place_id):
                        if await self.bot.api.check_root_place_id(transfer["old_place_id"], place_id):
                            #self.bot.stat_manager.stats[user_id]["currently_playing"]["game_instance_id"] = game_instance_id
                            await self.send_invite(guild, user_id, place_id, game_instance_id, transfer=True)
                        else:
                            #await self.bot.stat_manager.start_tracking_playtime(user_id, place_id, game_instance_id)
                            await self.send_invite(guild, user_id, place_id, game_instance_id)
                        continue

                    if guild_presences[user_id] != old_guild_presences[user_id]:
                        if await self.bot.api.check_root_place_id(old_guild_presences[user_id]["place_id"], place_id):
                            #self.bot.stat_manager.stats[user_id]["currently_playing"]["game_instance_id"] = (game_instance_id)
                            await self.send_invite(guild, user_id, place_id, game_instance_id, transfer=True)
                        else:
                            #await self.bot.stat_manager.start_tracking_playtime(user_id, place_id, game_instance_id)
                            await self.send_invite(guild, user_id, place_id, game_instance_id)
                else:
                    #await self.bot.stat_manager.start_tracking_playtime(user_id, place_id, game_instance_id)
                    await self.send_invite(guild, user_id, place_id, game_instance_id)

    async def process_updates(self):
        presences = await self.bot.presence_manager.get_all_presences("current")
        old_presences = await self.bot.presence_manager.get_all_presences("old")
        users = await self.bot.user_manager.get_all_users()

        for user_id in presences:
            status = presences[user_id]["user_status"]
            place_id = presences[user_id]["place_id"]
            game_instance_id = presences[user_id]["game_instance_id"]

            if user_id in old_presences:
                old_status = old_presences[user_id]["user_status"]
                old_place_id = old_presences[user_id]["place_id"]
                old_game_instance_id = old_presences[user_id]["game_instance_id"]

            if status in [0, 1]:
                if user_id in old_presences:
                    if old_status == 2 and user_id not in self.transfers:
                        await self.bot.transfer_manager.add_transfer(user_id, old_place_id, old_game_instance_id)
                    elif await self.bot.transfer_manager.check_transfer(user_id):
                        await self.bot.stat_manager.finish_tracking_playtime(user_id)
                        await self.bot.transfer_manager.remove_transfer(user_id)
                    elif await self.bot.stat_manager.check_currently_playing(user_id):
                        await self.bot.stat_manager.finish_tracking_playtime(user_id)
                print(f"{users[user_id]["username"]} is {'offline.' if status == 0 else 'on the Roblox website!'}")
            elif status == 2 and (game_instance_id is None or place_id is None):
                print(f"{users[user_id]["username"]} has their joins off, or you aren't following them.")
                print(f"   -> Follow them @ https://roblox.com/users/{user_id}/profile")
            elif status == 2:
                if user_id in old_presences:
                    if await self.bot.transfer_manager.check_transfer(user_id) == True:
                        transfer = await self.bot.transfer_manager.get_transfer(user_id)
                        if [transfer["old_place_id"], transfer["old_game_instance_id"]] == [place_id, game_instance_id]:
                            await self.bot.transfer_manager.remove_transfer(user_id)
                        else:
                            await self.bot.stat_manager.start_tracking_playtime(user_id, place_id)
                        continue

                    if presences[user_id] != old_presences[user_id]:
                        if not await self.bot.api.check_root_place_id(old_presences[user_id]["place_id"], place_id):
                            await self.bot.stat_manager.start_tracking_playtime(user_id, place_id)
                else:
                    await self.bot.stat_manager.start_tracking_playtime(user_id, place_id)
                print(f"{users[user_id]["username"]} is in a game: {underline}roblox://experiences/start?placeId={place_id}&gameInstanceId={game_instance_id}{end}")
            elif status == 3:
                print(f"{users[user_id]["username"]} is in Roblox Studio.")

    async def send_invite(self, guild, user_id, place_id, game_instance_id, transfer=False):
        if await self.bot.transfer_manager.check_transfer(user_id):
            await self.bot.transfer_manager.remove_transfer(user_id)

        if await self.bot.blacklist_manager.check_blacklist(guild, place_id):
            return

        #try:
        universe_id = await self.bot.api.get_universe_id(place_id)
        game = await self.bot.api.get_game_name(place_id)
        max_players = await self.bot.api.get_max_players(place_id)
        #except:
        #    return

        display_name = await self.bot.user_manager.get_display_name(user_id)
        username = await self.bot.user_manager.get_username(user_id)
        playtime_str = await self.bot.stat_manager.get_playtime_str(user_id, place_id, "both")
        playtime_str_current = await self.bot.stat_manager.get_playtime_str(user_id, place_id, "current")

        exclamation = "" if game_ends_in_punctuation(game) else "!"
        period = "" if game_ends_in_punctuation(game) else "."

        join_embed_url = f"https://join.rblxevnts.co/?placeId={place_id}&gameInstanceId={game_instance_id}"
        embed_title = f"{display_name} has joined a game!"
        embed_desc = f"**Join {display_name} (@{username}) in** *{game}*{exclamation}\nTotal playtime for this game: {playtime_str}\n-# Place ID: {place_id}"
        embed_color = green

        custom_title = {}
        if await self.bot.cgt_manager.check_custom_title(guild, universe_id):
            custom_title = await self.bot.cgt_manager.get_custom_title(guild, universe_id)
            embed_title = custom_title["title"].format(display_name)
            embed_color = int(custom_title["color"], 16)

        if transfer:
            if await self.bot.cgt_manager.check_custom_title(guild, universe_id):
                embed_title = f"{custom_title["title"].format(display_name)[:-1]} in a new server!"
            else:
                embed_title = f"{display_name} transferred servers!"
            embed_desc = f"{display_name} (@{username}) has transferred to a different server in *{game}*{period}\nSession playtime: {playtime_str_current}\nTotal playtime for this game: {playtime_str}\n-# Place ID: {place_id}"

        if max_players == 1:
            join_embed_url = None
            embed_desc = f"{display_name} (@{username}) is playing *{game}*{exclamation}\nHowever, you can't join them because the max server size is 1 player.\nTotal playtime for this game: {playtime_str}\n\n-# Place ID: {place_id}\n-# Game Instance ID: {game_instance_id}"
            if not await self.bot.cgt_manager.check_custom_title(guild, universe_id):
                embed_color = orange

        """
        joined = await self.check_joins(user_id, place_id, game_instance_id)
        if len(joined) > 0:
            embed_title += f" (+{len(joined)})"
            embed_desc = f"**{display_name} (@{username}) just joined:**"
            for user in joined:
                embed_desc += f"\n- {user[0]} (@{user[1]})"
            embed_desc += f"\n\nTotal playtime for this game: {playtime_str}\n**Join them** in *{game}* with the button below!\n-# Place ID: {place_id}"
        """

        await send_embed(self.bot, embed_title, embed_desc, embed_color, 1494129250343583898, join_embed_url)

    async def send_leave_message(self, guild, user_id, place_id, type):
        if await self.bot.blacklist_manager.check_blacklist(guild, place_id):
            return

        display_name = await self.bot.user_manager.get_display_name(user_id)
        username = await self.bot.user_manager.get_username(user_id)
        playtime_str = await self.bot.stat_manager.get_playtime_str(user_id, place_id, "current")
        playtime_str_2 = await self.bot.stat_manager.get_playtime_str(user_id, place_id, "both")
        universe_id = await self.bot.api.get_universe_id(place_id)
        game = await self.bot.api.get_game_name(place_id)
        period = "" if game_ends_in_punctuation(game) else "."

        if game is None:
            return

        embed_title = f"{display_name} left *{game}*{period}"
        embed_desc = f"Time played: {playtime_str}\nTotal playtime for this game: {playtime_str_2}"

        if type == "website":
            embed_desc = f"{display_name} (@{username}) is currently on the Roblox website or transferring between servers.\nIt's also possible that Roblox's APIs are showing this message in error.\n\nTime played: {playtime_str}\nTotal playtime for this game: {playtime_str_2}"
        
        if await self.bot.cgt_manager.check_custom_title(guild, universe_id):
            custom_title = await self.bot.cgt_manager.get_custom_title(guild, universe_id)
            embed_title = (
                custom_title["title"]
                .format(display_name)
                .replace(f"{display_name} is", f"{display_name} was")
                .replace("!", ".")
            )
            if type == "website":
                embed_desc = embed_desc.replace("is currently", f"has left *{game}*{period} They are")
            else:
                embed_desc = f"{display_name} (@{username}) has left *{game}*{period}\n" + embed_desc

        await send_embed(self.bot, embed_title, embed_desc, red, 1494129250343583898)