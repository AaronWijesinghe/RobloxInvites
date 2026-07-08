from storage.database import *

class BlacklistManager:
    def __init__(self):
        self.blacklist = load_data("blacklisted.json")
    
    async def add_blacklist(self, place_id, game_name):
        if place_id in self.blacklist:
            return False
        self.blacklist[place_id] = {"game": game_name}
        save_data(self.blacklist, "blacklisted.json")
        return True
    
    async def remove_blacklist(self, place_id):
        if place_id not in self.blacklist:
            return False
        del self.blacklist[place_id]
        save_data(self.blacklist, "blacklisted.json")
        return True