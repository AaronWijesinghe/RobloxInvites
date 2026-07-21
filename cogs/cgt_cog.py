import discord
from discord import app_commands
from discord.ext import commands
from database.database import *
from styling.ri_colors import *

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
            app_commands.Choice(name=game["game_name"], value=game["root_place_id"])
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
        success = await self.bot.cgt_manager.add_custom_title(place_id, title, hex_color, interaction.guild)
        if success == True:
            embed = discord.Embed(
                title="Added Custom Title!",
                description=f"**Place ID:** {place_id}\n**Title:** {title}\n**Hex Color:** #{hex_color.replace("#", "")}",
                color=int(hex_color, 16)
            )
        else:
            embed = discord.Embed(
                title="Error",
                description=success,
                color=red
            )
        await interaction.response.send_message(embed=embed)

    @cgt.command(name="remove", description="Removes a Custom Title!")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.autocomplete(place_id=cgt_game_autocomplete)
    async def remove_custom_title(
        self, 
        interaction: discord.Interaction, 
        place_id: int
    ):
        success = await self.bot.cgt_manager.remove_custom_title(place_id, interaction.guild)
        if success == True:
            embed = discord.Embed(
                title="Removed Custom Title!",
                description=f"Place ID: {place_id}",
                color=green
            )
        else:
            embed = discord.Embed(
                title="Error",
                description="That Place ID doesn't have a Custom Title associated with it.\nAdd a Custom Title with `/custom_title add`!",
                color=red
            )
        await interaction.response.send_message(embed=embed)

    @cgt.command(name="info", description="Gives information on a Custom Title")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.autocomplete(place_id=cgt_game_autocomplete)
    async def custom_title_info(
        self, 
        interaction: discord.Interaction, 
        place_id: int
    ):
        row = await self.bot.cgt_manager.get_custom_title_rpid(interaction.guild, place_id)
        if row is not None:
            embed = discord.Embed(
                title="Custom Title Info",
                description=f"**Place ID:** {place_id}\n**Title:** {row["title"]}\n**Hex Color:** #{row["color"].replace("#", "")}",
                color=int(row["color"], 16)
            )
        else:
            embed = discord.Embed(
                title="Error",
                description=f"That Place ID doesn't have a Custom Title associated with it.\nAdd a Custom Title with `/custom_title add`!",
                color=red
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(CGTCog(bot))