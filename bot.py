import os
import discord
import database
from database import Database
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

class RobloxInvitesBot(commands.Bot):
    def __init__(self, api, dev_guild):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        
        self.database = Database()
        self.api = api
        self.dev_guild = dev_guild

    async def setup_hook(self):
        await self.api.start()
        await self.database.initalize()

        self.user_manager = database.UserManager(self.database, self.api)
        #self.stat_manager = storage.StatManager(self.api, self.user_manager)
        #self.cgt_manager = storage.CGTManager(self.api)
        #self.blacklist_manager = storage.BlacklistManager()
        #self.channel_manager = storage.ChannelManager(self)

        self.load_extension("cogs.user_cog")
        
        self.tree.copy_global_to(guild=self.dev_guild)
        await self.tree.sync(guild=self.dev_guild)

    async def on_ready(self):
        print(f"{self.user} is online and ready!")