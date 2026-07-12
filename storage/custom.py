from storage.database import *
from styling.formatting import *

class CGTManager:
    def __init__(self, api):
        self.api = api
        self.custom_titles = load_data("custom_titles.json", {"version": 0, "titles": {}})
    
    async def add_custom_title(self, place_id, title, hex_color):
        place_id = get_number(place_id)
        hex_color = hex_color.lower().replace("#", "")
        if place_id not in self.api.cache["indexes"]:
            await self.api.cache_id(place_id)
        universe_id = self.api.cache["indexes"][place_id]

        self.custom_titles["titles"][str(universe_id)] = {
            "title": title,
            "color": hex_color,
            "game": await self.api.get_game_name(place_id),
            "place_id": place_id,
        }
        await save_data(self.custom_titles, "custom_titles.json")

    async def remove_custom_title(self, place_id):
        if place_id not in self.api.cache["indexes"]:
            await self.api.cache_id(place_id)
        universe_id = self.api.cache["indexes"][place_id]
        
        if str(universe_id) in self.custom_titles["titles"]:
            del self.custom_titles["titles"][str(universe_id)]
        await save_data(self.custom_titles, "custom_titles.json")