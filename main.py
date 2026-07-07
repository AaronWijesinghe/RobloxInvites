import asyncio
import roblox
import storage
import bot
from styling.ansi import *
import aiohttp

cookies = storage.load_data("cookies.json", None, False, "A cookie is required to use Roblox Invites.")
headers = {
    "Cookie": f".ROBLOSECURITY={cookies[0]}"
}


def clear():
    print("\033[2J\033[3J\033[H", end="")


async def loop():
    global api

    api = roblox.RobloxAPI()
    await api.start()

    times_checked = 1
    users = storage.UserManager(api)
    stats = bot.StatManager(api)
    notifier = bot.Notifier(api, users.users, stats)
    try:
        while True:
            try:
                clear()
                print(f"{gold}[Roblox Invites] [1.0.0b] [{times_checked}]{end}")
                user_ids = await users.get_user_ids()
                await notifier.process_updates(user_ids, headers)
                await asyncio.sleep(3)
                times_checked += 1
            except aiohttp.ClientResponseError as e:
                print(f"You've been rate limited! Status code: {e.status}")
                await asyncio.sleep(10)
    except asyncio.exceptions.CancelledError:
        await api.close()
    except KeyboardInterrupt:
        await api.close()
    finally:
        await api.close()


async def main():
    await loop()
        

if __name__ == "__main__":
    asyncio.run(main())