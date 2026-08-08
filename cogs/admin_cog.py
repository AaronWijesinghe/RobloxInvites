import discord
from discord import app_commands
from discord.ext import commands
from database.database import *
from styling.ri_colors import *
from subprocess import Popen
from datetime import datetime

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
            app_commands.Choice(name=data["username"], value=user_id)
            for user_id, data in users.items()
            if query.lower() in data["username"].lower()
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
        if not await self.bot.is_owner(interaction.user):
            await interaction.response.send_message(f"You are not the bot owner.")

        await interaction.response.defer(ephemeral=True)
        success = await interaction.client.user_manager.remove_user_id(user_id)
        if success == True:
            await interaction.followup.send(f"Removed this user from Roblox Invites.")
        else:
            await interaction.followup.send(f"This user isn't associated with Roblox Invites.")

    @admin.command(name="backup", description="Creates a .sql server backup")
    async def create_backup(
        self, 
        interaction: discord.Interaction
    ):
        if not await self.bot.is_owner(interaction.user):
            await interaction.response.send_message(f"You are not the bot owner.")

        await interaction.response.defer(ephemeral=True)
        filename = datetime.now().strftime("backup_%m-%d-%Y_%H-%M-%S.sql")
        backup_proc = Popen(["pg_dump", "-U", getpass.getuser(), "-d", "roblox_invites", "-f", f"./database/backups/{filename}"])
        exit_code = backup_proc.wait()
        if exit_code == 0:
            await interaction.followup.send("Successfully created a backup!")
        else:
            await interaction.followup.send(f"Couldn't create a backup. Exit code: {exit_code}")

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))