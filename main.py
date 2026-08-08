import os
import asyncio
import notifier
import discord
from bot import *
from dotenv import load_dotenv

load_dotenv()
headers = {
    "Cookie": f".ROBLOSECURITY={os.environ["cookie"]}"
}

version = "2.4.2"
patch_notes = """
Updated from __v{0}__ to __v{1}__

**Patch Notes:**
- Remove references to `dev_guild`
"""

if not os.path.exists("./database/backups/"):
    os.makedirs("./database/backups/")

api = notifier.API(headers)
bot = RobloxInvitesBot(api)
tracker_core = notifier.TrackerCore(bot)
bot.notifier = tracker_core
presence_tracker = notifier.PresenceTracker(bot, version, patch_notes)

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