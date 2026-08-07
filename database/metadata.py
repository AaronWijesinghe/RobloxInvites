class MetadataManager:
    def __init__(self, pool):
        self.pool = pool

    async def get_version(self):
        async with self.pool.acquire() as conn:
            saved_version = await conn.fetchval("""
                SELECT current_version
                FROM metadata
            """)

            if saved_version is None:
                return "0.0.0"
            else:
                return saved_version

    async def set_version(self, version_string):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO metadata (id, current_version)
                VALUES (1, $1)
                ON CONFLICT (id)
                DO UPDATE SET
                    current_version = EXCLUDED.current_version
            """, version_string)