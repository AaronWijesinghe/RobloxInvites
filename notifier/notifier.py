from styling.ri_colors import *
from styling.formatting import *
from storage.database import *
from notifier.send_embed import send_embed
from copy import deepcopy
import time

class Notifier:
    def __init__(self, bot):
        self.bot = bot
        self.user_presences = {}
        self.old_user_presences = load_data("old_user_presences.json")
        self.transfers = {}

    async def process_updates(self, user_ids, headers):
        new_presences = await self.bot.api.get_presences(user_ids, headers)
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
                            "start": time.time(),
                            "old_place_id": self.old_user_presences[user_id]["place_id"],
                            "old_game_instance_id": self.old_user_presences[user_id][
                                "game_instance_id"
                            ],
                            "username": self.bot.user_manager.users[user_id]["username"],
                        }
                    elif user_id in self.transfers:
                        if time.time() - self.transfers[user_id]["start"] > 5:
                            await self.send_leave_message(user_id, self.transfers[user_id]["old_place_id"], "absolute" if status == 0 else "website")
                            del self.transfers[user_id]
                    elif user_id in self.bot.stat_manager.stats:
                        if self.bot.stat_manager.stats[user_id]["currently_playing"] != {}:
                            self.bot.stat_manager.finish_tracking_playtime(user_id)
                print(f"{self.bot.user_manager.users[user_id]["display_name"]} is {'offline.' if status == 0 else 'on the Roblox website!'}")
            if status == 2 and (game_instance_id is None or place_id is None):
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
                    save_data(self.bot.stat_manager.stats, "stats.json")
                save_data(self.bot.user_manager.users, "users.json")
        self.old_user_presences = deepcopy(self.user_presences)
        save_data(self.old_user_presences, "old_user_presences.json")

    async def check_joins(self, user_id, place_id, game_instance_id):
        joined = []
        for uid in self.user_presences:
            if (
                self.user_presences[uid]["place_id"] == place_id
                and self.user_presences[uid]["game_instance_id"] == game_instance_id
                and uid != user_id
            ):
                joined += [(self.bot.user_manager.users[uid]["display_name"], self.bot.user_manager.users[uid]["username"])]
        return joined

    async def send_invite(self, user_id, place_id, game_instance_id, transfer=False):
        if str(user_id) in self.transfers:
            del self.transfers[str(user_id)]      

        if str(place_id) in self.bot.blacklist_manager.blacklist:
            return

        #try:
        universe_id = await self.bot.api.get_universe_id(place_id)
        game = await self.bot.api.get_game_name(place_id)
        max_players = await self.bot.api.get_max_players(place_id)
        #except:
        #    return

        display_name = self.bot.user_manager.users[user_id]["display_name"]
        username = self.bot.user_manager.users[user_id]["username"]
        playtime_str = await self.bot.stat_manager.get_playtime_str(user_id, place_id, "both")
        playtime_str_current = await self.bot.stat_manager.get_playtime_str(user_id, place_id, "current")

        exclamation = "" if game_ends_in_punctuation(game) else "!"
        period = "" if game_ends_in_punctuation(game) else "."

        join_embed_url = f"https://join.rblxevnts.co/?placeId={place_id}&gameInstanceId={game_instance_id}"
        embed_title = f"{display_name} has joined a game!"
        embed_desc = f"**Join {display_name} (@{username}) in** *{game}*{exclamation}\nTotal playtime for this game: {playtime_str}\n-# Place ID: {place_id}"
        embed_color = green

        if str(universe_id) in self.bot.cgt_manager.custom_titles["titles"]:
            embed_title = self.bot.cgt_manager.custom_titles["titles"][str(universe_id)]["title"].format(display_name)
            embed_color = int(self.bot.cgt_manager.custom_titles["titles"][str(universe_id)]["color"], 16)

        if transfer:
            if str(universe_id) in self.bot.cgt_manager.custom_titles["titles"]:
                embed_title = f"{self.bot.cgt_manager.custom_titles["titles"][str(universe_id)]["title"].format(display_name)[:-1]} in a new server!"
            else:
                embed_title = f"{display_name} transferred servers!"
            embed_desc = f"{display_name} (@{username}) has transferred to a different server in *{game}*{period}\nSession playtime: {playtime_str_current}\nTotal playtime for this game: {playtime_str}\n-# Place ID: {place_id}"

        if max_players == 1:
            join_embed_url = None
            embed_desc = f"{display_name} (@{username}) is playing *{game}*{exclamation}\nHowever, you can't join them because the max server size is 1 player.\nTotal playtime for this game: {playtime_str}\n\n-# Place ID: {place_id}\n-# Game Instance ID: {game_instance_id}"
            if str(universe_id) not in self.bot.cgt_manager.custom_titles["titles"]:
                embed_color = orange

        joined = await self.check_joins(user_id, place_id, game_instance_id)
        if len(joined) > 0:
            embed_title += f" (+{len(joined)})"
            embed_desc = f"**{display_name} (@{username}) just joined:**"
            for user in joined:
                embed_desc += f"\n- {user[0]} (@{user[1]})"
            embed_desc += f"\n\nTotal playtime for this game: {playtime_str}\n**Join them** in *{game}* with the button below!\n-# Place ID: {place_id}"

        await send_embed(self.bot, embed_title, embed_desc, embed_color, self.bot.channel_manager.channels["invite_channel"], join_embed_url)

    async def create_invite_card(self, user_id):
        username = self.bot.user_manager.users[user_id]["username"]
        display_name = self.bot.user_manager.users[user_id]["display_name"]
        place_id = self.user_presences[user_id]["place_id"]
        game_instance_id = self.user_presences[user_id]["game_instance_id"]

        if place_id == None:
            return ("Invite Card", f"{display_name} (@{username}) isn't playing anything right now.", "https://roblox.com/home")

        game = await self.bot.api.get_game_name(place_id)
        embed_title = f"Invite Card"
        embed_desc = f"**{display_name} (@{username}) has invited you** to play *{game}* with them!\n**Join them** with the button below."
        join_embed_url = f"https://join.rblxevnts.co/?placeId={place_id}&gameInstanceId={game_instance_id}"

        return (embed_title, embed_desc, join_embed_url)

    async def send_leave_message(self, user_id, place_id, type):
        if str(place_id) in self.bot.blacklist_manager.blacklist:
            return

        display_name = self.bot.user_manager.users[user_id]["display_name"]
        username = self.bot.user_manager.users[user_id]["username"]
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
        
        if str(universe_id) in self.bot.cgt_manager.custom_titles["titles"]:
            embed_title = (
                self.bot.cgt_manager.custom_titles["titles"][str(universe_id)]["title"]
                .format(display_name)
                .replace(f"{display_name} is", f"{display_name} was")
                .replace("!", ".")
            )
            if type == "website":
                embed_desc = embed_desc.replace("is currently", f"has left *{game}*{period} They are")
            else:
                embed_desc = f"{display_name} (@{username}) has left *{game}*{period}\n" + embed_desc

        await send_embed(self.bot, embed_title, embed_desc, red, self.bot.channel_manager.channels["invite_channel"])