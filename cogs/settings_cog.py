import discord
from discord import app_commands
from discord.ext import commands
from database.database import *

class SettingsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    channel = app_commands.Group(name="settings", description="Server settings for Roblox Invites")

    @channel.command(name="invites", description="Sets the channel ID for the invites channel")
    async def set_invite_channel(
        self, 
        interaction: discord.Interaction, 
        channel_id: str
    ):
        if not await self.bot.is_owner(interaction.user):
            await interaction.response.send_message(
                "You must be the bot owner to run this command.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        success = await interaction.client.settings_manager.set_channel(interaction.guild, "invite", channel_id)
        if success:
            await interaction.followup.send(f"Set the invite channel ID to `{channel_id}`.")
        else:
            await interaction.followup.send(f"Channel ID `{channel_id}` doesn't exist.")

    @channel.command(name="announcements", description="Sets the channel ID for the announcements channel")
    async def set_announcement_channel(
        self, 
        interaction: discord.Interaction, 
        channel_id: str
    ):
        if not await self.bot.is_owner(interaction.user):
            await interaction.response.send_message(
                "You must be the bot owner to run this command.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        success = await interaction.client.settings_manager.set_channel(interaction.guild, "announcement", channel_id)
        if success:
            await interaction.followup.send(f"Set the announcement channel ID to `{channel_id}`.")
        else:
            await interaction.followup.send(f"Channel ID `{channel_id}` doesn't exist.")

async def setup(bot: commands.Bot):
    await bot.add_cog(SettingsCog(bot))