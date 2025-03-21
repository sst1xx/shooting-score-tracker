import logging
import os
import sys
import asyncio
from telegram import Bot
from database import get_all_results, reset_database
from config import BOT_TOKEN, GROUP_ID

# Add parent directory to path to ensure imports work properly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(logs_dir, exist_ok=True)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename=os.path.join(logs_dir, 'leaderboard.log')
)
logger = logging.getLogger(__name__)

async def publish_leaderboard():
    """Publish leaderboard to the group chat and reset the database."""
    try:
        # Get all results from the database
        results = get_all_results()
        
        if not results:
            message = "Пока нет результатов для отображения."
        else:
            # Sort results by best_series (descending) and then by central_tens (descending)
            sorted_results = sorted(results, key=lambda x: (x[2], x[3]), reverse=True)
            
            # Format the leaderboard message
            message = "🏆 Таблица лидеров 🏆\n\n"
            for i, result in enumerate(sorted_results[:10], 1):  # Show top 10 results
                user_id, username, best_series, central_tens, photo_id, timestamp = result
                message += f"{i}. {username}: {best_series} очков, {central_tens} центральных десяток\n"

        # Send message to group
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=GROUP_ID, text=message)
        logger.info(f"Leaderboard published successfully to group {GROUP_ID}")
        
        # Reset the database for the next period
        reset_database()
        logger.info("Database reset for next period")
        
    except Exception as e:
        logger.error(f"Error publishing leaderboard: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(publish_leaderboard())
