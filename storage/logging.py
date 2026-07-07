import os
from datetime import datetime

def write_to_log(type, message):
    os.makedirs("./logs/", exist_ok=True)
    timestamp_date = datetime.now().strftime("%m-%d-%Y")
    timestamp_time = datetime.now().strftime("%H:%M:%S")
    open(f"./logs/{timestamp_date}.log", "a").write(f"[{timestamp_time}] [{type.upper()}] {message}\n")