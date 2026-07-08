import discord
from discord import app_commands
from discord.ext import commands
from storage.database import *
from storage.custom import *

class InviteCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="invite_user", description="Sends out an invite card for a given user!")
    async def invite_user(
        self, 
        interaction: discord.Interaction, 
        username: str
    ):
        await self.bot.user_manager.invite_user(username)
        await interaction.response.send_message(f"Sent an invite card!")

async def setup(bot: commands.Bot):
    await bot.add_cog(InviteCog(bot))