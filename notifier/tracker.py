import aiohttp
import asyncio
from styling.ansi import *

class PresenceTracker:
    def __init__(self, bot, version):
        self.bot = bot
        self.version = version
        self.user_presences = {}
        self.transfers = {}

    def clear(self):
        print("\033[2J\033[3J\033[H", end="")

    async def track(self):
        self.clear()
        print(f"{gold}[Roblox Invites] [{self.version}] [0]{end}")
        print("Waiting for the bot to get ready...")
        await self.bot.wait_until_ready()

        times_checked = 1
        while True:
            try:
                self.clear()
                print(f"{gold}[Roblox Invites] [{self.version}] [{times_checked}]{end}")
                user_ids = await self.bot.user_manager.get_user_ids()
                await self.bot.notifier.process_updates(user_ids)
                await asyncio.sleep(3)
                times_checked += 1
            except aiohttp.client_exceptions.ClientOSError:
                pass
            except aiohttp.ClientResponseError as e:
                self.clear()
                print(f"{gold}[Roblox Invites] [{self.version}] [{times_checked}]{end}")
                print(f"There's been a client response error! Status code: {e.status}")
                await asyncio.sleep(10)