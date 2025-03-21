# Configuration settings for the Telegram shooting bot

import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = os.getenv("GROUP_ID")
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/bot_database.sqlite")

# Ensure critical values are set
if not BOT_TOKEN:
    logging.critical("BOT_TOKEN not found in environment variables!")

if not GROUP_ID:
    logging.critical("GROUP_ID not found in environment variables!")


# logging.info(f"GROUP_ID из конфигурации: {GROUP_ID}")
