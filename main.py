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

version = "2.4.0"
patch_notes = """
Updated from __v{0}__ to __v{1}__

**Patch Notes:**
- Added admin commands
    - These commands can only be run by the bot owner.
   - Run `/admin backup` to create a server backup.
   - Run `/admin remove` to remove any user from Roblox Invites.
   - Run `/admin announce` to send an announcement to all announcement channels.
- Added a new invite link service at https://ropresencetools.github.io/
    - This should be much more reliable than https://rblxevents.co, which went down recently
- Added the ability to freeze your account
    - This stops sending invite messages to all servers you are in and stops accumulating playtime.
   - Run `/user freeze` to enable this privacy control.
   - Run `/user unfreeze` to disable this privacy control.
- Added the ability to hide invite messages in a specific server
    - This stops sending invite messages to a specific server, but still lets you accumulate playtime.
   - Run `/server pause_invites` to enable this privacy control.
   - Run `/server resume_invites` to disable this privacy control.
- Added update announcements like this one
- Fixed an issue where usercards would show the incorrect position for the Since Last Snapshot leaderboard
- Fixed an issue where leaving a server wouldn't properly unlink that user from that server
- Fixed the text in the Remove Blacklist success embed
- Optimized searching within commands
- Roblox Invites is now a part of RoPresenceTools (GitHub)
"""

dev_guild = discord.Object(id=os.environ["guild"])
api = notifier.API(headers)
bot = RobloxInvitesBot(api, dev_guild)
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