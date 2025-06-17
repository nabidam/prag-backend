import logging
from logging.handlers import TimedRotatingFileHandler
from telethon import TelegramClient, events
from telethon import functions, types
from telethon.tl.functions.channels import GetForumTopicsRequest
from telethon.tl.functions.messages import CheckChatInviteRequest
from telethon.tl.functions.users import GetFullUserRequest
from dotenv import load_dotenv
import datetime
import os
import sqlite3
# from utils import save_message
from time import sleep
import shutil
import re

load_dotenv()

log_dir = "logs"

# Ensure log directory exists
os.makedirs(log_dir, exist_ok=True)

# Set up the logger
logger = logging.getLogger("telegram_logger")
logger.setLevel(logging.INFO)

# Create a log handler that rotates daily
log_file_handler = TimedRotatingFileHandler(
    filename=os.path.join(log_dir, "telegram_logs.log"),
    when="midnight",  # Rotate logs at midnight every day
    interval=1,
    backupCount=7,  # Keep the last 7 log files
    utc=True,  # Use UTC time for logging
)

# Set the log file name format to include the date in the filename
log_file_handler.suffix = "%Y-%m-%d"

# Set the format for log messages
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
log_file_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(log_file_handler)

# Use your own values from my.telegram.org
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")


# Regex pattern for Telegram proxy links
proxy_pattern = re.compile(r'https://t\.me/proxy\?server=[^\s]+')

# Create the client
client = TelegramClient(
    "session_name", api_id, api_hash, proxy=("socks5", "127.0.0.1", 1080)
)


@client.on(events.NewMessage)
async def proxy_listener_handler(event):
    message = event.message.message
    matches = proxy_pattern.findall(message)
    for link in matches:
        try:
            # TODO: store in db
            print(f"Stored proxy link: {link}")
        except Exception as e:
            print(f"Failed to store link: {link}\nError: {e}")


async def main():
    await client.start()
    logger.info("Connected to Telegram API")

    await client.run_until_disconnected()
    # logger.info("Group history fetched successfully")


with client:
    client.loop.run_until_complete(main())
