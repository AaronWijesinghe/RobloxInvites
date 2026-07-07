async def send_embed(api, title, desc, color, webhook):
    data = {
        "embeds": [{"title": title, "description": desc, "color": color}],
        "components": [],
    }
    async with api.session.post(webhook, json=data) as response:
        response.raise_for_status()
        return None