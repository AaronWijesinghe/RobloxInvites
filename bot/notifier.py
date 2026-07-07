import aiohttp
import asyncio
from styling.discord_colors import *
from styling.formatting import *
from storage.database import *
from bot.send_embed import send_embed
from copy import deepcopy
import time

class Notifier:
    def __init__(self, api, users, stats):
        self.api = api
        self.users = users
        self.stats = stats
        self.user_presences = {}
        self.old_user_presences = load_data("old_user_presences.json")
        self.transfers = {}

    async def process_updates(self, user_ids, headers):
        new_presences = await self.api.get_presences(user_ids, headers)
        for i, user_id in enumerate(user_ids):
            self.user_presences[str(user_id)] = {
                "game_instance_id": new_presences["userPresences"][i]["gameId"],
                "place_id": new_presences["userPresences"][i]["placeId"],
                "status": new_presences["userPresences"][i]["userPresenceType"],
            }

        for user_id, presence in self.user_presences.items():
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
                            "username": self.users[user_id]["username"],
                        }
                    elif user_id in self.transfers:
                        if time.time() - self.transfers[user_id]["start"] > 5:
                            await self.send_leave_message(user_id, self.transfers[user_id]["old_place_id"], "absolute" if status == 0 else "website")
                            del self.transfers[user_id]
                    elif user_id in self.stats.stats:
                        if self.stats.stats[user_id]["currently_playing"] != {}:
                            self.stats.finish_tracking_playtime(user_id)
                print(f"{self.users[user_id]["display_name"]} is {'offline.' if status == 0 else 'on the Roblox website!'}")
            if status == 2 and (game_instance_id is None or place_id is None):
                print(f"{self.users[user_id]["display_name"]} has their joins off, or you aren't following them.")
                print(f"   -> Follow them @ https://roblox.com/users/{user_id}/profile")
            elif status == 2:
                if user_id in self.old_user_presences:
                    if user_id in self.transfers:
                        if [
                            self.transfers[user_id]["old_place_id"],
                            self.transfers[user_id]["old_game_instance_id"],
                        ] == [place_id, game_instance_id]:
                            del self.transfers[user_id]
                        elif await self.api.check_root_place_id(self.transfers[user_id]["old_place_id"], place_id):
                            self.stats.stats[user_id]["currently_playing"]["game_instance_id"] = game_instance_id
                            await self.send_invite(user_id, place_id, game_instance_id, transfer=True)
                        else:
                            await self.stats.start_tracking_playtime(user_id, place_id, game_instance_id)
                            await self.send_invite(user_id, place_id, game_instance_id)
                        continue

                    if self.user_presences[user_id] != self.old_user_presences[user_id]:
                        if await self.api.check_root_place_id(self.old_user_presences[user_id]["place_id"], place_id):
                            self.stats.stats[user_id]["currently_playing"]["game_instance_id"] = (game_instance_id)
                            await self.send_invite(user_id, place_id, game_instance_id, transfer=True)
                        else:
                            await self.stats.start_tracking_playtime(user_id, place_id, game_instance_id)
                            await self.send_invite(user_id, place_id, game_instance_id)
                else:
                    await self.stats.start_tracking_playtime(user_id, place_id, game_instance_id)
                    await self.send_invite(user_id, place_id, game_instance_id)
                print(f"{self.users[user_id]["display_name"]} is in a game: {underline}roblox://experiences/start?placeId={place_id}&gameInstanceId={game_instance_id}{end}")
            elif status == 3:
                print(f"{self.users[user_id]["display_name"]} is in Roblox Studio.")
        self.old_user_presences = deepcopy(self.user_presences)
        save_data(self.old_user_presences, "old_user_presences.json")

    async def send_invite(self, user_id, place_id, game_instance_id, transfer=False):
        if str(user_id) in self.transfers:
            del self.transfers[str(user_id)]       

        #try:
        universe_id = await self.api.get_universe_id(place_id)
        game = await self.api.get_game_name(place_id)
        max_players = await self.api.get_max_players(place_id)
        #except:
        #    return

        display_name = self.users[user_id]["display_name"]
        username = self.users[user_id]["username"]
        playtime_str = await self.stats.get_playtime_str(user_id, place_id, "both")
        playtime_str_current = await self.stats.get_playtime_str(user_id, place_id, "current")

        exclamation = "" if game_ends_in_punctuation(game) else "!"
        period = "" if game_ends_in_punctuation(game) else "."

        join_embed_url = f"https://join.rblxevnts.co/?placeId={place_id}&gameInstanceId={game_instance_id}"
        game_url = f"roblox://experiences/start?placeId={place_id}&gameInstanceId={game_instance_id}"
        embed_title = f"{display_name} has joined a game!"
        embed_desc = f"**Join {display_name} (@{username}) in** *{game}*{exclamation}\nTotal playtime for this game: {playtime_str}\n\nClick [this link]({join_embed_url}) to join, or copy + paste the URL below in your browser:\n-# {game_url}"
        embed_color = green

        if transfer:
            embed_title = f"{display_name} transferred servers!"
            embed_desc = f"{display_name} (@{username}) has transferred to a different server in *{game}*{period}\nSession playtime: {playtime_str_current}\nTotal playtime for this game: {playtime_str}\n\nClick [this link]({join_embed_url}) to join, or copy + paste the URL below in your browser:\n-# {game_url}"

        if max_players == 1:
            embed_color = orange
            embed_desc = f"{display_name} (@{username}) is playing *{game}*{exclamation}\nHowever, you can't join them because the max server size is 1 player.\nTotal playtime for this game: {playtime_str}\n\n-# {game_url}"

        display_name = self.users[user_id]["display_name"]
        await send_embed(self.api, embed_title, embed_desc, embed_color, "https://discord.com/api/webhooks/1494129302067744871/HLpZhKOb_6ucO98Zp9pjEGrndSN0RhJWZoZJRL9M-soWZkF-bd4P2xQve0DGI69bAgYg")

    async def send_leave_message(self, user_id, place_id, type):
        global webhook

        display_name = self.users[user_id]["display_name"]
        username = self.users[user_id]["username"]
        playtime_str = await self.stats.get_playtime_str(user_id, place_id, "current")
        playtime_str_2 = await self.stats.get_playtime_str(user_id, place_id, "both")
        universe_id = await self.api.get_universe_id(place_id)
        game = await self.api.get_game_name(place_id)
        period = "" if game_ends_in_punctuation(game) else "."

        if game is None:
            return

        embed_title = f"{display_name} left *{game}*{period}"
        embed_desc = f"Time played: {playtime_str}\nTotal playtime for this game: {playtime_str_2}"

        if type == "website":
            embed_desc = f"{display_name} (@{username}) is currently on the Roblox website or transferring between servers.\nIt's also possible that Roblox's APIs are showing this message in error.\n\nTime played: {playtime_str}\nTotal playtime for this game: {playtime_str_2}"
        await send_embed(self.api, embed_title, embed_desc, red, "https://discord.com/api/webhooks/1494129302067744871/HLpZhKOb_6ucO98Zp9pjEGrndSN0RhJWZoZJRL9M-soWZkF-bd4P2xQve0DGI69bAgYg")