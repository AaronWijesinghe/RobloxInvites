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
        users = await interaction.client.user_manager.search_users(interaction.guild, query)
        return [
            app_commands.Choice(name=user, value=id)
            for id, user in users
        ]

    user = app_commands.Group(name="user", description="User commands")

    @user.command(name="add", description="Adds a new user to Roblox Invites")
    async def add_user(
        self, 
        interaction: discord.Interaction, 
        username: str
    ):
        if not await self.bot.is_owner(interaction.user):
            await interaction.response.send_message(
                "You must be the bot owner to run this command.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        await interaction.client.user_manager.add_user(username, interaction.guild)
        await interaction.followup.send(f"Added user @{username} to Roblox Invites!")

    @user.command(name="remove", description="Removes a user from the current server")
    @app_commands.autocomplete(user_id=user_autocomplete)
    async def remove_user(
        self, 
        interaction: discord.Interaction, 
        user_id: int
    ):
        if not await self.bot.is_owner(interaction.user):
            await interaction.response.send_message(
                "You must be the bot owner to run this command.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        await interaction.client.user_manager.remove_user(user_id, interaction.guild)
        await interaction.followup.send(f"Removed user with ID {user_id} from this guild. Hope you had a great time!")

    #@app_commands.autocomplete(user_id=user_autocomplete)
    @user.command(name="remove_global", description="Removes a user from Roblox Invites")
    async def remove_user_global(
        self, 
        interaction: discord.Interaction, 
        user_id: int
    ):
        if not await self.bot.is_owner(interaction.user):
            await interaction.response.send_message(
                "You must be the bot owner to run this command.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        await interaction.client.user_manager.remove_user_global(user_id)
        await interaction.followup.send(f"Removed user with ID {user_id} from Roblox Invites. Hope you had a great time!")

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