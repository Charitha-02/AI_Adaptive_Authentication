import os
from datetime import datetime

LOG_FOLDER = "storage/authentication_logs"
LOG_FILE = os.path.join(LOG_FOLDER, "logs.txt")

os.makedirs(LOG_FOLDER, exist_ok=True)

def log_event(email, status):
    with open(LOG_FILE, "a") as file:
        file.write(
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {email} | {status}\n"
        )