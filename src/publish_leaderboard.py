import logging
import os
import sys
import datetime
from telegram import Bot
from database import get_leaderboard, reset_database
from config import BOT_TOKEN, GROUP_ID

# Add parent directory to path to ensure imports work properly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs/leaderboard.log')
)
logger = logging.getLogger(__name__)

async def publish_leaderboard():
    """Publish leaderboard to the group chat and reset the database."""
    try:
        # Check if this is the right week to publish (every two weeks)
        current_week = datetime.date.today().isocalendar()[1]
        if current_week % 2 == 0:  # Only publish on even weeks
            logger.info("Not publishing this week (odd week number)")
            return

        # Get leaderboard data
        leaderboard = get_leaderboard()
        if not leaderboard:
            message = "No results yet."
        else:
            message = "🏆 Top 10 Results 🏆\n\n"
            for idx, row in enumerate(leaderboard, start=1):
                username, best_series, central_tens = row
                message += f"{idx}. {username}: Best Series = {best_series}, Central Tens = {central_tens}\n"

        # Send message to group
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=GROUP_ID, text=message)
        logger.info("Leaderboard published successfully")
        
        # Reset the database for the next period
        reset_database()
        logger.info("Database reset for next period")
        
    except Exception as e:
        logger.error(f"Error publishing leaderboard: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(publish_leaderboard())
