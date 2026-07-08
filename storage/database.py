import os
import json
from styling.ansi import *
from storage.logging import write_to_log

"""
# maybe add async storage later?
async def save_json_file(data):
    json_string = json.dumps(data, indent=4)
    async with aiofiles.open("data.json", mode="w") as f:
        await f.write(json_string)
"""

def load_data(
    file: str,
    no_exist_data: dict | list | None = {},
    no_exist_ok: bool = True,
    no_exist_message: str = "",
) -> dict | list:
    if os.path.exists(f"./data/{file}"):
        return json.loads(open(f"./data/{file}").read())
    elif no_exist_ok:
        write_to_log("info", f"Created file './data/{file}' with data '{no_exist_data}'")
        save_data(no_exist_data, file)
        return no_exist_data
    elif not no_exist_ok and no_exist_message != "":
        write_to_log("fatal", no_exist_message)
        save_data(no_exist_data, file)
        print(f"{underline}{no_exist_message}{end}")
        exit()
    return {}


def save_data(data, file):
    open(f"./data/{file}", "w").write(json.dumps(data, indent=2))