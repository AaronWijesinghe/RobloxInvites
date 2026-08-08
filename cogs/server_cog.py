import discord
from discord import app_commands
from discord.ext import commands
from database.database import *
from styling.ri_colors import *

class ServerCog(commands.Cog):
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

    server = app_commands.Group(
        name="server",
        description="Server commands",
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

    @server.command(name="link", description="Links your account with the current server")
    async def link(
        self, 
        interaction: discord.Interaction
    ):
        await interaction.response.defer(ephemeral=True)
        success = await interaction.client.user_manager.link_user(interaction.user, interaction.guild)
        if success == True:
            await interaction.followup.send(f"Successfully added you to this server!")
        else:
            await interaction.followup.send(success)

    @server.command(name="unlink", description="Unlinks you from the current server")
    async def unlink(
        self, 
        interaction: discord.Interaction,
    ):
        await interaction.response.defer(ephemeral=True)
        success = await interaction.client.user_manager.unlink_user(interaction.user, interaction.guild)
        if success == True:
            await interaction.followup.send(f"Removed you from this server. Hope you had a great time!")
        else:
            await interaction.followup.send(f"You don't have a Roblox account associated with Roblox Invites.\nAdd one with `/user add`!")

    @server.command(name="user_stats", description="Shows a user's statistics in a given server")
    @app_commands.autocomplete(user_id=user_autocomplete)
    async def get_user_card(
        self, 
        interaction: discord.Interaction, 
        user_id: int
    ):
        await interaction.response.defer()
        message_title, message_content = await interaction.client.leaderboard_manager.get_user_stats(interaction.guild, user_id)
        embed = discord.Embed(
            title=message_title,
            description=message_content,
            color=discord.Color.dark_gold() if message_title != "Error" else red
        )
        await interaction.followup.send(embed=embed)

    @server.command(name="pause_invites", description="Pauses sending invites pertaining to your account in the current server")
    async def pause_invites(
        self, 
        interaction: discord.Interaction
    ):
        await interaction.response.defer(ephemeral=True)
        success = await interaction.client.user_manager.modify_server_invites(interaction.user, interaction.guild, 1)
        if success == True:
            await interaction.followup.send(f"Successfully paused messages related to your account in this server!")
        else:
            await interaction.followup.send(success)

    @server.command(name="resume_invites", description="Resumes sending invites pertaining to your account in the current server")
    async def resume_invites(
        self, 
        interaction: discord.Interaction
    ):
        await interaction.response.defer(ephemeral=True)
        success = await interaction.client.user_manager.modify_server_invites(interaction.user, interaction.guild, 0)
        if success == True:
            await interaction.followup.send(f"Successfully resumed messages related to your account in this server!")
        else:
            await interaction.followup.send(success)

async def setup(bot: commands.Bot):
    await bot.add_cog(ServerCog(bot))