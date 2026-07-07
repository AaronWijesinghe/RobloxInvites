from datetime import datetime
from storage.database import *
from styling.formatting import *
from aiohttp_retry import RetryClient, ExponentialRetry

class CGTManager:
    def __init__(self, api):
        self.api = api
    
    async def add_custom_title(self, place_id, message, hex_color):
        place_id = get_number(place_id)
        hex_color = hex_color.lower().replace("#", "")
        if place_id not in self.api.cache["indexes"]:
            self.api.cache_id(place_id)
        universe_id = await self.api["indexes"]

        ct_path = "./server/custom_titles.json"
        ct = json.loads(open(ct_path).read())
        ct["titles"][str(universe_id)] = {
            "title": message,
            "color": hex_color,
            "game": await self.api.get_game_name(place_id),
            "place_id": place_id,
        }
        open(ct_path, "w").write(json.dumps(ct, indent=2))
    
