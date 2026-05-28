import json
import os
import sys

import requests


def clear():
    print("\033[2J\033[3J\033[H", end="")


def get_number(string):
    new_string = ""
    scanning_place_id = False
    for char in string:
        if char.isdigit() and not scanning_place_id:
            scanning_place_id = True
            new_string += char
        elif char.isdigit() and scanning_place_id:
            new_string += char
        elif not char.isdigit() and scanning_place_id:
            break
    return new_string


gold = "\033[0;33m"
end = "\033[0m"

version = "1.4.0"
os.chdir(os.path.dirname(__file__))

clear()
print(f"{gold}[Custom Title Wizard]{end}")
print(f"Version v{version} | Supports Roblox Invites v4.4.1\n")
place_id = get_number(input("Enter the place ID or the link of a Roblox game: "))
message = input("Enter the custom title ({0} represents the display name of a user): ")
hex_color = input("Enter the hex code of the color: ").lower()
name = input("Enter game name: ")
universe_id = requests.get(
    f"https://apis.roblox.com/universes/v1/places/{place_id}/universe"
).json()["universeId"]

ct_path = "/Users/aaron/Desktop/Projects/RobloxInvites/server/custom_titles.json"
ct = json.loads(open(ct_path).read())
ct["titles"][str(universe_id)] = {
    "title": message,
    "color": hex_color,
    "game": name,
    "place_id": place_id,
}
open(ct_path, "w").write(json.dumps(ct, indent=4))

if input("\nDone! Add another custom title (y/N)? ") == "y":
    os.execv(sys.executable, [sys.executable] + sys.argv)
