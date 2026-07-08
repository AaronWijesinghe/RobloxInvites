import discord
from discord import app_commands
from discord.ext import commands
from storage.database import *
from storage.custom import *
from styling.discord_colors import *

class CGTCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="add_custom_title", description="Adds a Custom Title!")
    async def add_custom_title(
        self, 
        interaction: discord.Interaction, 
        title: str, 
        place_id: str,
        hex_color: str
    ):
        await self.bot.cgt_manager.add_custom_title(place_id, title, hex_color)
        await interaction.response.send_message(f"**Added custom title!**\nPlace ID: {place_id}\nTitle: {title}\nHex Color: #{hex_color}")

    @app_commands.command(name="remove_custom_title", description="Removes a Custom Title!")
    async def remove_custom_title(
        self, 
        interaction: discord.Interaction, 
        place_id: str
    ):
        if not await self.bot.is_owner(interaction.user):
            await interaction.response.send_message(
                "You must be the bot owner to run this command.",
                ephemeral=True,
            )
            return
        await self.bot.cgt_manager.remove_custom_title(place_id)
        await interaction.response.send_message(f"**Removed custom title!**\nPlace ID: {place_id}")

async def setup(bot: commands.Bot):
    await bot.add_cog(CGTCog(bot))