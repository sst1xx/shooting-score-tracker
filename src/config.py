# Configuration settings for the Telegram shooting bot

import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Ensure critical values are set
if not BOT_TOKEN:
    logging.critical("BOT_TOKEN not found in environment variables!")

if not CHAT_ID:
    logging.critical("CHAT_ID not found in environment variables!")
