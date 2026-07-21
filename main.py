import os
import asyncio
import notifier
import discord
import database
from bot import *
from styling.ansi import *
from styling.ri_colors import *
from dotenv import load_dotenv

load_dotenv()
version = "2.1.1"
headers = {
    "Cookie": f".ROBLOSECURITY={os.environ["cookie"]}"
}

dev_guild = discord.Object(id=os.environ["guild"])
api = notifier.API(headers)
bot = RobloxInvitesBot(api, dev_guild)
tracker_core = notifier.TrackerCore(bot)
bot.notifier = tracker_core
presence_tracker = notifier.PresenceTracker(bot, version)

async def main():
    try:
        await asyncio.gather(
            bot.start(os.environ["token"]),
            presence_tracker.track()
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