import discord
from discord import app_commands
from discord.ext import commands
from database.database import *

class CGTCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cgt_game_autocomplete(
        self,
        interaction: discord.Interaction,
        query: str,
    ) -> list[app_commands.Choice[str]]:
        game_list = await self.bot.cgt_manager.get_cgt_games(interaction.guild)

        return [
            app_commands.Choice(name=game["game_name"], value=game["place_id"])
            for game in game_list
            if query.lower() in game["game_name"].lower()
        ][:25]

    cgt = app_commands.Group(name="custom_title", description="Custom game title commands")

    @cgt.command(name="add", description="Adds a Custom Title!")
    async def add_custom_title(
        self, 
        interaction: discord.Interaction, 
        title: str, 
        place_id: int,
        hex_color: str
    ):
        await self.bot.cgt_manager.add_custom_title(place_id, title, hex_color, interaction.guild)
        await interaction.response.send_message(f"**Added custom title!**\nPlace ID: {place_id}\nTitle: {title}\nHex Color: #{hex_color.replace("#", "")}")

    @cgt.command(name="remove", description="Removes a Custom Title!")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.autocomplete(place_id=cgt_game_autocomplete)
    async def remove_custom_title(
        self, 
        interaction: discord.Interaction, 
        place_id: int
    ):
        await self.bot.cgt_manager.remove_custom_title(place_id, interaction.guild)
        await interaction.response.send_message(f"**Removed custom title!**\nPlace ID: {place_id}")

async def setup(bot: commands.Bot):
    await bot.add_cog(CGTCog(bot))