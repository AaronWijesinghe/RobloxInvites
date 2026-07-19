import discord
from discord import app_commands
from discord.ext import commands
from database.database import *

class UserCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def user_autocomplete(
        self,
        interaction: discord.Interaction,
        query: str,
    ) -> list[app_commands.Choice[str]]:
        users = await interaction.client.user_manager.get_guild_users(interaction.guild)
        return [
            app_commands.Choice(name=user["username"], value=user["user_id"])
            for user in users
            if query.lower() in user["username"].lower()
        ]

    user = app_commands.Group(name="user", description="User commands")

    @user.command(name="add", description="Adds a new user to Roblox Invites")
    async def add_user(
        self, 
        interaction: discord.Interaction, 
        username: str
    ):
        await interaction.response.defer()
        try:
            success = await interaction.client.user_manager.add_user(username, interaction.user, interaction.guild)
        except Exception as e:
            import traceback
            traceback.print_exc()
        if success == True:
            await interaction.followup.send(f"Added user @{username} to Roblox Invites!")
        else:
            await interaction.followup.send(success)

    @user.command(name="remove", description="Removes you from the current server")
    async def remove_user(
        self, 
        interaction: discord.Interaction, 
    ):
        await interaction.response.defer()
        success = await interaction.client.user_manager.remove_user(interaction.user, interaction.guild)
        if success == True:
            await interaction.followup.send(f"Removed you from this guild. Hope you had a great time!")
        else:
            await interaction.followup.send(f"You don't have a Roblox account associated with Roblox Invites.\nAdd one with `/user add`!")

    """
    @user.command(name="stats", description="Gets a user's stat card")
    @app_commands.autocomplete(user_id=user_autocomplete)
    async def get_user_card(
        self, 
        interaction: discord.Interaction, 
        user_id: str
    ):
        await interaction.response.defer()
        message_title, message_content = await self.bot.stat_manager.get_user_stats(user_id)
        embed = discord.Embed(
            title=message_title,
            description=message_content,
            color=discord.Color.dark_gold()
        )
        await interaction.followup.send(embed=embed)
    """

async def setup(bot: commands.Bot):
    await bot.add_cog(UserCog(bot))