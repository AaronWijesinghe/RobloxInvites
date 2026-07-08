import discord
from discord import app_commands
from discord.ext import commands
from storage.database import *
from storage.custom import *


class LeaderboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    leaderboard = app_commands.Group(name="leaderboard", description="Leaderboard commands")

    async def all_games_autocomplete(
        self,
        interaction: discord.Interaction,
        query: str,
    ) -> list[app_commands.Choice[str]]:
        game_cache = {
            interaction.client.api.cache["caches"][universe_id]["name"]: interaction.client.api.cache["caches"][universe_id]["root_place_id"]
            for universe_id in interaction.client.api.cache["caches"].keys()
        }

        return [
            app_commands.Choice(name=name, value=str(value))
            for (name, value) in list(game_cache.items())
            if query.lower() in name.lower()
        ][:25]

    @leaderboard.command(name="all", description="Sends this server's all-time playtime leaderboard")
    async def all_time_user_leaderboard(
        self, 
        interaction: discord.Interaction
    ):
        (message_title, message_content) = await self.bot.stat_manager.get_alltime_user_leaderboard()
        embed = discord.Embed(
            title=message_title,
            description=message_content,
            color=discord.Color.dark_gold()
        )
        await interaction.response.send_message(embed=embed)

    @leaderboard.command(name="weekly", description="Sends this server's weekly playtime leaderboard")
    async def weekly_user_leaderboard(
        self,
        interaction: discord.Interaction
    ):
        (message_title, message_content) = await self.bot.stat_manager.get_weekly_user_leaderboard()
        embed = discord.Embed(
            title=message_title,
            description=message_content,
            color=discord.Color.dark_gold()
        )
        await interaction.response.send_message(embed=embed)

    @leaderboard.command(name="game", description="Sends this server's all-time playtime leaderboard for a game")
    @app_commands.autocomplete(place_id=all_games_autocomplete)
    async def all_time_game_leaderboard(
        self, 
        interaction: discord.Interaction,
        place_id: str
    ):
        (message_title, message_content) = await self.bot.stat_manager.get_game_leaderboard(place_id)
        embed = discord.Embed(
            title=message_title,
            description=message_content,
            color=discord.Color.dark_gold()
        )
        await interaction.response.send_message(embed=embed)

    @leaderboard.command(name="save", description="Saves a snapshot of user data for weekly leaderboards")
    async def save_period(
        self, 
        interaction: discord.Interaction, 
    ):
        if not await self.bot.is_owner(interaction.user):
            await interaction.response.send_message(
                "You must be the bot owner to run this command.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        await self.bot.stat_manager.save_period()
        await interaction.followup.send("Saved the current data to a snapshot!")

    @leaderboard.command(name="remove", description="Removes the last saved user snapshot")
    async def remove_last_period(
        self, 
        interaction: discord.Interaction, 
    ):
        if not await self.bot.is_owner(interaction.user):
            await interaction.response.send_message(
                "You must be the bot owner to run this command.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        await self.bot.stat_manager.remove_last_period()
        await interaction.followup.send("Removed the last saved snapshot.")

async def setup(bot: commands.Bot):
    await bot.add_cog(LeaderboardCog(bot))