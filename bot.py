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
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)
        
        self.db = Database()
        self.api = api
        self.dev_guild = dev_guild

    async def setup_hook(self):
        await self.api.start()
        await self.db.initalize()

        self.api.pool = self.db.pool

        self.metadata_manager = database.MetadataManager(self.db.pool)
        self.user_manager = database.UserManager(self.db.pool, self.api)
        self.presence_manager = database.PresenceManager(self.db.pool, self.api, self.user_manager)
        self.transfer_manager = database.TransferManager(self.db.pool)
        self.cgt_manager = database.CGTManager(self.db.pool, self.api)
        self.blacklist_manager = database.BlacklistManager(self.db.pool, self.api)
        self.settings_manager = database.SettingsManager(self.db.pool, self)
        self.stat_manager = database.StatManager(self.db.pool, self.api, self.user_manager)
        self.snapshot_manager = database.SnapshotManager(self.db.pool, self, self.api)
        self.leaderboard_manager = database.LeaderboardManager(self.db.pool, self, self.api)

        await self.load_extension("cogs.help_cog")
        await self.load_extension("cogs.user_cog")
        await self.load_extension("cogs.cgt_cog")
        await self.load_extension("cogs.blacklist_cog")
        await self.load_extension("cogs.settings_cog")
        await self.load_extension("cogs.leaderboard_cog")
        await self.load_extension("cogs.server_cog")

        await self.tree.sync()

    async def on_ready(self):
        for guild in self.guilds:
            await self.db.create_guild(guild)
        print(f"{self.user} is online and ready!")

    async def on_member_remove(self, member):
        await self.user_manager.remove_user(member, member.guild)