import discord
from discord import app_commands
from discord.ext import commands
from database.database import *
from styling.ri_colors import *

class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def user_autocomplete(
        self,
        interaction: discord.Interaction,
        query: str,
    ) -> list[app_commands.Choice[str]]:
        users = await interaction.client.user_manager.get_all_users()
        return [
            app_commands.Choice(name=user["username"], value=user["user_id"])
            for user in users
            if query.lower() in user["username"].lower()
        ]

    admin = app_commands.Group(
        name="admin",
        description="Admin commands",
        allowed_installs=app_commands.AppInstallationType(
            guild=True,
            user=False
        ),
        allowed_contexts=app_commands.AppCommandContext(
            guild=True,
            dm_channel=False,
            private_channel=False
        )
    )

    @admin.command(name="remove", description="Removes a user from Roblox Invites")
    @app_commands.autocomplete(user_id=user_autocomplete)
    async def admin_remove_user(
        self, 
        interaction: discord.Interaction,
        user_id: int
    ):
        if not self.bot.is_owner():
            await interaction.response.send_message(f"You are not the owner of this bot.")

        await interaction.response.defer(ephemeral=True)
        success = await interaction.client.user_manager.remove_user_id(user_id)
        if success == True:
            await interaction.followup.send(f"Removed this user from Roblox Invites.")
        else:
            await interaction.followup.send(f"This user isn't associated with Roblox Invites.")

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))