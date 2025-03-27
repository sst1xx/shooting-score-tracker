# Configuration settings for the Telegram shooting bot

import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Database configuration
DATA_DIR = os.environ.get('DATA_DIR', './data')
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, 'scoreboard.db')

# Ensure critical values are set
if not BOT_TOKEN:
    logging.critical("BOT_TOKEN not found in environment variables!")

if not CHAT_ID:
    logging.critical("CHAT_ID not found in environment variables!")
