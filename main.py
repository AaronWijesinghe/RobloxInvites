import os
import asyncpg
import aiohttp
import asyncio
import notifier
from bot import *
from styling.ansi import *
from styling.ri_colors import *
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
version = "2.0.0"
headers = {
    "Cookie": f".ROBLOSECURITY={os.environ["cookie"]}"
}

patch_notes = f"""
Updated to __v{version}__

**Changes:**
- Patch notes will be updated on release.
"""


def clear():
    print("\033[2J\033[3J\033[H", end="")


async def presence_tracker(bot):
    clear()
    print(f"{gold}[Roblox Invites] [{version}] [0]{end}")
    print("Waiting for the bot to get ready...")
    await bot.wait_until_ready()

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


api = notifier.RobloxAPI(headers)
bot = RobloxInvitesBot(api, os.environ["guild"])

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
        await bot.api.close()
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())