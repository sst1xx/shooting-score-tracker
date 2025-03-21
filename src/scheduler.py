import schedule
import time
import threading
import datetime
from database import get_leaderboard, reset_database
from config import BOT_TOKEN, GROUP_ID
from telegram import Bot

# Global variable to track which week to publish
week_counter = 0

def publish_leaderboard():
    global week_counter
    week_counter += 1
    
    # Only publish every 2 weeks (when counter is odd)
    if week_counter % 2 == 1:
        leaderboard = get_leaderboard()
        if not leaderboard:
            message = "No results yet."
        else:
            message = "Top 10 Results:\n"
            for idx, row in enumerate(leaderboard, start=1):
                username, best_series, central_tens = row
                message += f"{idx}. {username}: Best Series = {best_series}, Central Tens = {central_tens}\n"

        bot = Bot(token=BOT_TOKEN)
        bot.send_message(chat_id=GROUP_ID, text=message)
        reset_database()

def run_scheduler():
    """
    Run the schedule in a loop on a separate thread.
    """
    while True:
        schedule.run_pending()
        time.sleep(1)

def schedule_leaderboard_publish(application):
    """
    Schedule the leaderboard publication every Monday at 09:00,
    but only publish every other week.
    """
    schedule.every().monday.at("09:00").do(publish_leaderboard)
    thread = threading.Thread(target=run_scheduler, daemon=True)
    thread.start()