import discord

async def send_embed(bot, title, desc, color, url=None):
    embed = discord.Embed(
        title=title,
        description=desc,
        color=color
    )

    view = discord.ui.View()
    if url is not None:
        join_btn = discord.ui.Button(label="Join in Roblox", url=url)
        view.add_item(join_btn)

    channel = bot.get_channel(1524150418878234705)
    await channel.send(embed=embed, view=view)