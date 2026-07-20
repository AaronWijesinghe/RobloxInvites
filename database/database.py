import asyncpg
import getpass
from pathlib import Path

class Database:
    def __init__(self):
        self.pool = None

    async def initalize(self):
        await self.connect()
        await self.create_tables()

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            user=getpass.getuser(),
            password="",
            database="roblox_invites",
            host="localhost"
        )
    
    async def create_tables(self):
        schema_path = Path(__file__).parent / ".." / "database" / "schema.sql"
        async with self.pool.acquire() as conn:
            await conn.execute(schema_path.read_text())
    
    async def create_guild(self, guild):
        async with self.pool.acquire() as conn:
            await conn.execute(f"""
                INSERT INTO guild_settings (guild_id)
                VALUES ($1)
                ON CONFLICT (guild_id)
                DO NOTHING
            """, guild.id)