from storage.database import *

class ChannelManager:
    def __init__(self):
        self.channels = load_data("channels.json", {"announcement_channel": 0, "invite_channel": 0}, False, "You must save valid channel IDs to /data/channels.json to use Roblox Invites.")