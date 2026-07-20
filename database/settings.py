class SettingsManager:
    def __init__(self, database, bot):
        self.bot = bot
        self.database = database
        self.pool = database.pool

    async def get_channel(self, guild, channel_type):
        async with self.pool.acquire() as conn:
            channel = await conn.fetchval(f"""
                SELECT {channel_type}_channel
                FROM guild_settings
                WHERE guild_id = $1
            """, guild.id)
        return channel

    async def set_channel(self, guild, channel_type, channel):
        async with self.pool.acquire() as conn:
            await conn.execute(f"""
                UPDATE guild_settings
                SET {channel_type}_channel = $2
                WHERE guild_id = $1
            """, guild.id, channel.id)

        await channel.send(f"The {channel_type} channel has been set to this channel.")
        return True