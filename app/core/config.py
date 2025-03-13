import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    DB_NAME = os.getenv('DB_NAME')
    APP_PORTS = os.getenv('APP_PORTS')[-4:]
    WEBHOOK_HOST = os.getenv('WEBHOOK_HOST')
    WEBHOOK_PATH = os.getenv('WEBHOOK_PATH')
    WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
    FILE_PATH = os.getenv('FILE_PATH')
