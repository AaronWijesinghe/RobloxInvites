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
        return [
            app_commands.Choice(name=game_name["game"], value=str(place_id))
            for place_id, game_name in interaction.client.blacklist_manager.blacklist.items()
            if query.lower() in game_name["game"].lower()
        ][:25]

    @blacklist.command(name="add", description="Adds a game to the blacklist")
    async def add_blacklist(
        self, 
        interaction: discord.Interaction, 
        place_id: str,
        game_name: str
    ):
        if not await self.bot.is_owner(interaction.user):
            await interaction.response.send_message(
                "You must be the bot owner to run this command.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        success = await interaction.client.blacklist_manager.add_blacklist(interaction.guild, place_id, game_name)
        if success:
            await interaction.followup.send(f"Added place ID {place_id} to the blacklist.")
        else:
            await interaction.followup.send(f"Place ID {place_id} is already in the blacklist!")

    @blacklist.command(name="remove", description="Removes a game from the blacklist")
    @app_commands.autocomplete(place_id=blacklisted_games_autocomplete)
    async def remove_blacklist(
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

        await interaction.response.defer()
        success = await interaction.client.blacklist_manager.remove_blacklist(interaction.guild, place_id)
        if success:
            await interaction.followup.send(f"Removed place ID {place_id} from the blacklist.")
        else:
            await interaction.followup.send(f"Place ID {place_id} is not in the blacklist!")

async def setup(bot: commands.Bot):
    await bot.add_cog(BlacklistCog(bot))