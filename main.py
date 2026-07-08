import os
import aiohttp
import asyncio
import discord
import notifier
import storage
from styling.ansi import *
from dotenv import load_dotenv
from discord.ext import commands

cookies = storage.load_data("cookies.json", None, False, "A cookie is required to use Roblox Invites.")
headers = {
    "Cookie": f".ROBLOSECURITY={cookies[0]}"
}


def clear():
    print("\033[2J\033[3J\033[H", end="")


async def presence_tracker(bot):
    await bot.wait_until_ready()

    times_checked = 1
    tracker = notifier.Notifier(bot)
    bot.notifier = tracker
    while True:
        try:
            clear()
            print(f"{gold}[Roblox Invites] [1.0.0b] [{times_checked}]{end}")
            user_ids = await bot.user_manager.get_user_ids()
            await tracker.process_updates(user_ids, headers)
            await asyncio.sleep(3)
            times_checked += 1
        except aiohttp.ClientResponseError as e:
            clear()
            print(f"{gold}[Roblox Invites] [1.0.0b] [{times_checked}]{end}")
            print(f"There's been a client response error! Status code: {e.status}")
            await asyncio.sleep(10)
        except asyncio.exceptions.CancelledError:
            return
        except KeyboardInterrupt:
            return


class RobloxInvitesBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.api = notifier.RobloxAPI()
        await self.api.start()

        self.user_manager = storage.UserManager(self.api)
        self.stat_manager = storage.StatManager(self.api, self.user_manager)
        self.cgt_manager = storage.CGTManager(self.api)
        self.blacklist_manager = storage.BlacklistManager()

        await self.load_extension("cogs.cgt_cog")
        await self.load_extension("cogs.user_cog")
        await self.load_extension("cogs.leaderboard_cog")
        await self.load_extension("cogs.blacklist_cog")
        await self.load_extension("cogs.invite_cog")
        
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)


bot = RobloxInvitesBot()
MY_GUILD = discord.Object(id=os.environ["guild"])

@bot.event
async def on_ready():
    print(f"{bot.user} is online and ready!")


async def main():
    load_dotenv()

    try:
        await asyncio.gather(
            bot.start(os.environ["token"]),
            presence_tracker(bot)
        )
    finally:
        await bot.api.close()
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())