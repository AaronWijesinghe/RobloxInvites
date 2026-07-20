import discord
from discord import app_commands
from discord.ext import commands
from database.database import *

class SettingsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    channel = app_commands.Group(name="settings", description="Server settings for Roblox Invites")

    @channel.command(name="invites", description="Sets the channel ID for the invites channel")
    @app_commands.default_permissions(manage_guild=True)
    async def set_invite_channel(
        self, 
        interaction: discord.Interaction, 
        channel: discord.TextChannel
    ):
        await interaction.response.defer()
        success = await interaction.client.settings_manager.set_channel(interaction.guild, "invite", channel)
        if success:
            await interaction.followup.send(f"Set the invite channel to https://discord.com/channels/{interaction.guild.id}/{channel.id}")
        else:
            await interaction.followup.send(f"Channel ID `{channel.id}` doesn't exist.")

    @channel.command(name="announcements", description="Sets the channel ID for the announcements channel")
    @app_commands.default_permissions(manage_guild=True)
    async def set_announcement_channel(
        self, 
        interaction: discord.Interaction, 
        channel: discord.TextChannel
    ):
        await interaction.response.defer()
        success = await interaction.client.settings_manager.set_channel(interaction.guild, "announcement", channel)
        if success:
            await interaction.followup.send(f"Set the announcement channel to https://discord.com/channels/{interaction.guild.id}/{channel.id}")
        else:
            await interaction.followup.send(f"Channel ID `{channel.id}` doesn't exist.")

async def setup(bot: commands.Bot):
    await bot.add_cog(SettingsCog(bot))