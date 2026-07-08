import discord
from discord import app_commands
from discord.ext import commands
from storage.database import *
from storage.custom import *

class InviteCog(commands.Cog):
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

    @app_commands.command(name="invite_user", description="Sends out an invite card for a given user!")
    @app_commands.autocomplete(user_id=user_autocomplete)
    async def invite_user(
        self, 
        interaction: discord.Interaction, 
        user_id: str
    ):
        await interaction.response.defer()
        (message_title, message_content, join_url) = await interaction.client.notifier.create_invite_card(user_id)
        
        embed = discord.Embed(
            title=message_title,
            description=message_content,
            color=discord.Color.dark_purple()
        )
        
        view = discord.ui.View()
        join_btn = discord.ui.Button(label="Join in Roblox", url=join_url)
        view.add_item(join_btn)

        await interaction.followup.send(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(InviteCog(bot))