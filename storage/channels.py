from storage.database import *

class ChannelManager:
    def __init__(self, bot):
        self.bot = bot
        self.channels = load_data("channels.json", {"announcement_channel": 0, "invite_channel": 0}, False, "You must save valid channel IDs to /data/channels.json to use Roblox Invites.")
    
    async def set_channel(self, channel_type, channel_id):
        if not channel_id.isdigit():
            return False
        else:
            channel_id = int(channel_id)

        try:
            channel = self.bot.get_channel(channel_id)
            channel.send(f"The {channel} channel has been set to this channel.")
        except:
            return False

        if channel_type in ["announcement", "invite"]:
            self.channels[f"{channel_type}_channel"] = channel_id
        save_data(self.channels, "channels.json")
        return True
