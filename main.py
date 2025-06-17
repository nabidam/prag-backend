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

from sqlmodel import Session, SQLModel, create_engine, Field, select, func, text, update, Relationship

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Annotated
from fastapi import Depends, Body

load_dotenv()


# -------------- LOGGING -------------- #

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


# -------------- INIT -------------- #

# Use your own values from my.telegram.org
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

DB_USER = os.environ.get("DB_USER")
DB_USER_PASS = os.environ.get("DB_USER_PASS")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_DATABASE = os.environ.get("DB_DATABASE")
DB_URI = f"mysql+mysqlconnector://{DB_USER}:{
    DB_USER_PASS}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"


# -------------- MODELS -------------- #

class TGProxy(SQLModel, table=True):
    __tablename__ = "tg_proxies"

    id: int | None = Field(default=None, primary_key=True, index=True)
    msg_id: str = Field(unique=True, nullable=False)
    sender_id: str = Field(unique=True, nullable=False)
    raw_msg: str | None = None
    msg: str | None = None
    proxy: str | None = None
    likes: int = Field(default=0)
    dislikes: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.now)


engine = create_engine(DB_URI, echo=True)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_db():
    with Session(engine) as session:
        try:
            yield session
        finally:
            session.close()


# -------------- TG CLIENT -------------- #


# Create the client
client = TelegramClient(
    "session_name", API_ID, API_HASH, proxy=("socks5", "127.0.0.1", 1080)
)


# -------------- MISC -------------- #

# Regex pattern for Telegram proxy links
proxy_pattern = re.compile(r'https://t\.me/proxy\?server=[^\s]+')


@client.on(events.NewMessage)
async def proxy_listener_handler(event):
    message = event.message.message
    matches = proxy_pattern.findall(message)
    for link in matches:
        try:
            print(event)
            print(event.message)
            print(event.sender_id)
            # TODO: store in db
            print(f"Stored proxy link: {link}")
        except Exception as e:
            print(f"Failed to store link: {link}\nError: {e}")


# -------------- APP -------------- #


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    await client.start()
    await client.run_until_disconnected()
    yield
    await client.disconnect()


app = FastAPI(lifespan=lifespan)


origins = [
    # "https://divineaty.navidam.ir",
    # "https://faalosher.navidam.ir",
    # "https://faalosher.creativeaty.club",
    # "http://localhost",
    # "http://localhost:5173",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DependsDB = Annotated[Session, Depends(get_db)]


# -------------- ROUTES -------------- #


@app.get("/")
def read_root():
    return {"Hello": "World"}


# async def main():
#     await client.start()
#     logger.info("Connected to Telegram API")

#     await client.run_until_disconnected()
#     # logger.info("Group history fetched successfully")


# with client:
#     client.loop.run_until_complete(main())
