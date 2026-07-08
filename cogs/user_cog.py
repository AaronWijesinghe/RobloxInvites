import discord
from discord import app_commands
from discord.ext import commands
from storage.database import *
from storage.custom import *

class UserCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def user_autocomplete(
        self,
        interaction: discord.Interaction,
        query: str,
    ) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=user["username"], value=id)
            for id, user in interaction.client.user_manager.users.items()
            if query.lower() in user["username"].lower()
        ][:25]

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
        await interaction.client.user_manager.add_user(username)
        await interaction.followup.send(f"Added user @{username} to Roblox Invites!")

    @user.command(name="remove", description="Removes a user from Roblox Invites")
    @app_commands.autocomplete(user_id=user_autocomplete)
    async def remove_user(
        self, 
        interaction: discord.Interaction, 
        user_id: str
    ):
        if not await self.bot.is_owner(interaction.user):
            await interaction.response.send_message(
                "You must be the bot owner to run this command.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        await interaction.client.user_manager.remove_user(user_id)
        await interaction.followup.send(f"Removed user @{interaction.client.user_manager.users[user_id]["username"]} from Roblox Invites. Hope you had a great time!")

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

async def setup(bot: commands.Bot):
    await bot.add_cog(UserCog(bot))