import discord
from discord import app_commands
from discord.ext import commands
from database.database import *

class LeaderboardCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    leaderboard = app_commands.Group(name="leaderboard", description="Leaderboard commands")
    game = app_commands.Group(name="game", description="Game-related leaderboard commands", parent=leaderboard)

    async def all_games_autocomplete(
        self,
        interaction: discord.Interaction,
        query: str,
    ) -> list[app_commands.Choice[str]]:
        game_list = await self.bot.api.get_cached_games(interaction.guild)

        return [
            app_commands.Choice(name=game["game_name"], value=game["root_place_id"])
            for game in game_list
            if query.lower() in game["game_name"].lower()
        ][:25]

    @leaderboard.command(name="all", description="Sends this server's all-time playtime leaderboard")
    async def all_time_user_leaderboard(
        self, 
        interaction: discord.Interaction
    ):
        (message_title, message_content) = await interaction.client.leaderboard_manager.get_alltime_user_leaderboard(interaction.guild)
        embed = discord.Embed(
            title=message_title,
            description=message_content,
            color=discord.Color.dark_gold()
        )
        await interaction.response.send_message(embed=embed)

    @leaderboard.command(name="last_snapshot", description="Sends this server's playtime leaderboard since last snapshot")
    async def ls_leaderboard(
        self,
        interaction: discord.Interaction
    ):
        (message_title, message_content) = await interaction.client.leaderboard_manager.get_ls_user_leaderboard(interaction.guild)
        embed = discord.Embed(
            title=message_title,
            description=message_content,
            color=discord.Color.dark_gold()
        )
        await interaction.response.send_message(embed=embed)

    @game.command(name="all", description="Sends this server's all-time playtime leaderboard for a game")
    @app_commands.autocomplete(place_id=all_games_autocomplete)
    async def all_time_game_leaderboard(
        self, 
        interaction: discord.Interaction,
        place_id: int
    ):
        (message_title, message_content) = await interaction.client.leaderboard_manager.get_alltime_game_leaderboard(interaction.guild, place_id)
        embed = discord.Embed(
            title=message_title,
            description=message_content,
            color=discord.Color.dark_gold()
        )
        await interaction.response.send_message(embed=embed)

    @game.command(name="last_snapshot", description="Sends this server's playtime leaderboard for a game since the last saved snapshot")
    @app_commands.autocomplete(place_id=all_games_autocomplete)
    async def ls_game_leaderboard(
        self, 
        interaction: discord.Interaction,
        place_id: int
    ):
        (message_title, message_content) = await interaction.client.leaderboard_manager.get_ls_game_leaderboard(interaction.guild, place_id)
        embed = discord.Embed(
            title=message_title,
            description=message_content,
            color=discord.Color.dark_gold()
        )
        await interaction.response.send_message(embed=embed)

    @leaderboard.command(name="save", description="Saves a snapshot of user data for weekly leaderboards")
    @app_commands.default_permissions(manage_guild=True)
    async def save_period(
        self, 
        interaction: discord.Interaction, 
    ):
        await interaction.response.defer()
        await interaction.client.snapshot_manager.save_snapshot(interaction.guild)
        await interaction.followup.send("Saved the current data to a snapshot!")

    @leaderboard.command(name="remove", description="Removes the last saved user snapshot")
    @app_commands.default_permissions(manage_guild=True)
    async def remove_last_period(
        self, 
        interaction: discord.Interaction, 
    ):
        await interaction.response.defer()
        await interaction.client.snapshot_manager.remove_last_snapshot(interaction.guild)
        await interaction.followup.send("Removed the last saved snapshot.")
        
async def setup(bot: commands.Bot):
    await bot.add_cog(LeaderboardCog(bot))