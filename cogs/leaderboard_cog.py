import discord
from discord import app_commands
from discord.ext import commands
from storage.database import *
from storage.custom import *


class LeaderboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

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

    @app_commands.command(name="leaderboard", description="Sends this server's all-time playtime leaderboard")
    async def all_time_user_leaderboard(
        self, 
        interaction: discord.Interaction
    ):
        message_content = await self.bot.stat_manager.get_alltime_user_leaderboard()
        embed = discord.Embed(
            title="All-Time Playtime Leaderboard",
            description=message_content,
            color=discord.Color.dark_gold()
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="game_leaderboard", description="Sends this server's all-time playtime leaderboard for a game")
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

async def setup(bot: commands.Bot):
    await bot.add_cog(LeaderboardCog(bot))