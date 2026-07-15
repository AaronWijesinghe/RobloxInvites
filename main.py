import os
import aiohttp
import asyncio
import discord
import notifier
import storage
from styling.ansi import *
from styling.ri_colors import *
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
version = "1.3.5"
cookies = storage.load_data("cookies.json", None, False, "A cookie is required to use Roblox Invites.")
headers = {
    "Cookie": f".ROBLOSECURITY={cookies[0]}"
}

display_patch_notes = False
saved_version = storage.load_data("version.json", {"version": "0.0.0"})
patch_notes = f"""
Updated from __v{saved_version["version"]}__ to __v{version}__

**Changes:**
- A leave message should now send if you enter Roblox Studio while playing a game
"""
if saved_version["version"] != version:
    display_patch_notes = True
    saved_version["version"] = version
storage.save_data_blocking(saved_version, "version.json")


def clear():
    print("\033[2J\033[3J\033[H", end="")


async def presence_tracker(bot):
    clear()
    print(f"{gold}[Roblox Invites] [{version}] [0]{end}")
    print("Waiting for the bot to get ready...")
    await bot.wait_until_ready()

    if display_patch_notes:
        embed = discord.Embed(
            title="Roblox Invites has been updated!",
            description=patch_notes,
            color=discord.Color.blue()
        )
    else:
        embed = discord.Embed(
            title="Roblox Invites has been started!",
            color=discord.Color.blue()
        )
    channel = bot.get_channel(bot.channel_manager.channels["announcement_channel"])
    await channel.send(embed=embed)

    times_checked = 1
    tracker = notifier.Notifier(bot)
    bot.notifier = tracker
    while True:
        try:
            clear()
            print(f"{gold}[Roblox Invites] [{version}] [{times_checked}]{end}")
            user_ids = await bot.user_manager.get_user_ids()
            await tracker.process_updates(user_ids)
            await asyncio.sleep(3)
            times_checked += 1
        except aiohttp.client_exceptions.ClientOSError:
            pass
        except aiohttp.ClientResponseError as e:
            clear()
            print(f"{gold}[Roblox Invites] [{version}] [{times_checked}]{end}")
            print(f"There's been a client response error! Status code: {e.status}")
            await asyncio.sleep(10)


class RobloxInvitesBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.api = notifier.RobloxAPI(headers)
        await self.api.start()

        self.user_manager = storage.UserManager(self.api)
        self.stat_manager = storage.StatManager(self.api, self.user_manager)
        self.cgt_manager = storage.CGTManager(self.api)
        self.blacklist_manager = storage.BlacklistManager()
        self.channel_manager = storage.ChannelManager(self)

        await self.load_extension("cogs.cgt_cog")
        await self.load_extension("cogs.user_cog")
        await self.load_extension("cogs.leaderboard_cog")
        await self.load_extension("cogs.blacklist_cog")
        await self.load_extension("cogs.invite_cog")
        await self.load_extension("cogs.channel_cog")
        
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)


bot = RobloxInvitesBot()
MY_GUILD = discord.Object(id=os.environ["guild"])

@bot.event
async def on_ready():
    print(f"{bot.user} is online and ready!")

async def main():
    try:
        await asyncio.gather(
            bot.start(os.environ["token"]),
            presence_tracker(bot)
        )
    except KeyboardInterrupt:
        pass
    except asyncio.exceptions.CancelledError:
        pass
    finally:
        embed = discord.Embed(
            title="Roblox Invites has been stopped.",
            color=red
        )
        channel = bot.get_channel(bot.channel_manager.channels["announcement_channel"])
        await channel.send(embed=embed)

        await bot.api.close()
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())