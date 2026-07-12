import os
import json
import aiofiles
from styling.ansi import *
from storage.logging import *

def save_data_blocking(data, file):
    with open(f"./data/{file}", "w") as f:
        f.write(json.dumps(data, indent=2))


async def save_data(data, file):
    data_json = json.dumps(data, indent=2)
    async with aiofiles.open(f"./data/{file}", mode="w") as f:
        await f.write(data_json)


def load_data(
    file: str,
    no_exist_data: dict | list | None = {},
    no_exist_ok: bool = True,
    no_exist_message: str = "",
) -> dict | list:
    if os.path.exists(f"./data/{file}"):
        with open(f"./data/{file}") as f:
            return json.loads(f.read())
    elif no_exist_ok:
        write_to_log_blocking("info", f"Created file './data/{file}' with data '{no_exist_data}'")
        save_data_blocking(no_exist_data, file)
        return no_exist_data
    elif not no_exist_ok and no_exist_message != "":
        write_to_log_blocking("fatal", no_exist_message)
        save_data_blocking(no_exist_data, file)
        print(f"{underline}{no_exist_message}{end}")
        raise SystemExit
    return {}