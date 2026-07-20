import discord
from discord import app_commands
from discord.ext import commands
from database.database import *

class BlacklistCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    blacklist = app_commands.Group(name="blacklist", description="Blacklist commands")

    async def blacklisted_games_autocomplete(
        self,
        interaction: discord.Interaction,
        query: str,
    ) -> list[app_commands.Choice[str]]:
        blacklisted_games = await interaction.client.blacklist_manager.get_blacklisted_games(interaction.guild)
        return [
            app_commands.Choice(name=game["game_name"], value=game["place_id"])
            for game in blacklisted_games
            if query.lower() in game["game_name"].lower()
        ][:25]

    @blacklist.command(name="add", description="Adds a game to the blacklist")
    @app_commands.default_permissions(manage_guild=True)
    async def add_blacklist(
        self, 
        interaction: discord.Interaction, 
        place_id: int,
        game_name: str
    ):
        await interaction.response.defer()
        success = await interaction.client.blacklist_manager.add_blacklist(interaction.guild, place_id, game_name)
        if success:
            await interaction.followup.send(f"Added place ID {place_id} to the blacklist.")
        else:
            await interaction.followup.send(f"Place ID {place_id} is already in the blacklist!")

    @blacklist.command(name="remove", description="Removes a game from the blacklist")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.autocomplete(place_id=blacklisted_games_autocomplete)
    async def remove_blacklist(
        self, 
        interaction: discord.Interaction, 
        place_id: int
    ):
        await interaction.response.defer()
        success = await interaction.client.blacklist_manager.remove_blacklist(interaction.guild, place_id)
        if success:
            await interaction.followup.send(f"Removed place ID {place_id} from the blacklist.")
        else:
            await interaction.followup.send(f"Place ID {place_id} is not in the blacklist!")

async def setup(bot: commands.Bot):
    await bot.add_cog(BlacklistCog(bot))