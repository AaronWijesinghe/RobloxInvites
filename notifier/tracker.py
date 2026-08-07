import aiohttp
import asyncio
from styling.ansi import *
import discord

class PresenceTracker:
    def __init__(self, bot, version):
        self.bot = bot
        self.version = version

    def clear(self):
        print("\033[2J\033[3J\033[H", end="")

    async def track(self):
        self.clear()
        print(f"{gold}[Roblox Invites] [{self.version}] [0]{end}")
        print("Waiting for the bot to get ready...")
        await self.bot.wait_until_ready()

        saved_version = await self.bot.metadata_manager.get_version()
        if saved_version != self.version:
            for guild in self.bot.guilds:
                announcement_channel = await self.bot.settings_manager.get_channel(guild, "announcement")

                embed = discord.Embed(
                    title="An update has been issued!",
                    description="description",
                    color=discord.Color.blue()
                )

                try:
                    channel = self.bot.get_channel(announcement_channel)
                    await channel.send(embed=embed)
                except:
                    pass

            await self.bot.metadata_manager.set_version(self.version)

        times_checked = 1
        while True:
            try:
                self.clear()
                print(f"{gold}[Roblox Invites] [{self.version}] [{times_checked}]{end}")
                user_ids = await self.bot.user_manager.get_all_user_ids()
                if len(user_ids) == 0:
                    print("No users are currently being tracked.")
                else:
                    await self.bot.presence_manager.save_presences("current")
                    for guild in self.bot.guilds:
                        await self.bot.notifier.send_guild_updates(guild)
                    await self.bot.notifier.process_updates()
                    await self.bot.presence_manager.save_presences("old")
                    await self.bot.user_manager.remove_deleted_users()
                await asyncio.sleep(3)
                times_checked += 1
            except aiohttp.client_exceptions.ClientOSError:
                pass
            except aiohttp.ClientResponseError as e:
                self.clear()
                print(f"{gold}[Roblox Invites] [{self.version}] [{times_checked}]{end}")
                print(f"There's been a client response error! Status code: {e.status}")
                await asyncio.sleep(10)
            except aiohttp.client_exceptions.ClientConnectorCertificateError:
                self.clear()
                print(f"{gold}[Roblox Invites] [{self.version}] [{times_checked}]{end}")
                print(f"Couldn't connect to Roblox's servers.")
                print("Make sure your certificates are up to date and that Roblox isn't blocked on your network.")
                await asyncio.sleep(5)
            except aiohttp.client_exceptions.ClientResponseError:
                self.clear()
                print(f"{gold}[Roblox Invites] [{self.version}] [{times_checked}]{end}")
                print(f"Couldn't connect to Roblox's servers.")
                print("The tracker will wait 10 seconds before continuing.")
                await asyncio.sleep(10)