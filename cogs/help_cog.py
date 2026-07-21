import discord
from discord import app_commands
from discord.ext import commands
from database.database import *

help_message = """
**Welcome to Roblox Invites!**
I send invites to other server members when you join a game on Roblox, and track your playtime across Roblox games.
To add yourself to the bot, run `/user add` followed by your username and verify if needed.
To remove yourself from the current server, run `/user remove`.
To update your user info if you change your username/display name, run `/user update_info`.

**For server admins:**
Run `/settings invites` to set the channel where invites are sent.
Run `/settings announcements` to set the channel where announcements are sent.
To remove a Custom Title, run `/custom_title remove`.
To add or remove a blacklisted place ID, run `/blacklist [add | remove]`.
To save/delete snapshots, run `/leaderboard [save | remove]`.
"""

class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="Gives some basic info on how to use the bot")
    async def help(
        self, 
        interaction: discord.Interaction
    ):
        embed = discord.Embed(
            title="Help",
            description=help_message,
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))