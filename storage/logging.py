import os
import aiofiles
from datetime import datetime

def write_to_log_blocking(type, message):
    os.makedirs("./logs/", exist_ok=True)
    timestamp_date = datetime.now().strftime("%m-%d-%Y")
    timestamp_time = datetime.now().strftime("%H:%M:%S")
    with open(f"./logs/{timestamp_date}.log", "a") as f:
        f.write(f"[{timestamp_time}] [{type.upper()}] {message}\n")

async def write_to_log(type, message):
    os.makedirs("./logs/", exist_ok=True)
    timestamp_date = datetime.now().strftime("%m-%d-%Y")
    timestamp_time = datetime.now().strftime("%H:%M:%S")
    async with aiofiles.open(f"./logs/{timestamp_date}.log", mode="a") as f:
        await f.write(f"[{timestamp_time}] [{type.upper()}] {message}\n")