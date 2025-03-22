import logging
import os
import sys
import asyncio
from telegram import Bot
from database import get_all_results, reset_database
from config import BOT_TOKEN, CHAT_ID

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
            # Filter results into three groups
            pro_results = [r for r in results if r[2] >= 93]
            semi_pro_results = [r for r in results if 80 <= r[2] <= 92]
            amateur_results = [r for r in results if r[2] <= 79]
            
            # Sort each group by best_series and total_tens
            pro_sorted = sorted(pro_results, key=lambda x: (x[2], x[3]), reverse=True)[:10]
            semi_pro_sorted = sorted(semi_pro_results, key=lambda x: (x[2], x[3]), reverse=True)[:10]
            amateur_sorted = sorted(amateur_results, key=lambda x: (x[2], x[3]), reverse=True)[:10]
            
            # Format the message
            message = "🏆 Таблица лидеров по всем группам 🏆\n\n"
            
            # Pro group
            message += "👑 Группа Профи 👑\n"
            if not pro_sorted:
                message += "В этой группе пока нет результатов.\n\n"
            else:
                for i, result in enumerate(pro_sorted, 1):
                    _, username, best_series, total_tens, *_ = result
                    message += f"{i}. {username}: {best_series} очков, {total_tens}*\n"
                message += "\n"
            
            # Semi-pro group
            message += "🥈 Группа Полупрофи 🥈\n"
            if not semi_pro_sorted:
                message += "В этой группе пока нет результатов.\n\n"
            else:
                for i, result in enumerate(semi_pro_sorted, 1):
                    _, username, best_series, total_tens, *_ = result
                    message += f"{i}. {username}: {best_series} очков, {total_tens}\n"
                message += "\n"
            
            # Amateur group
            message += "🥉 Группа Любители 🥉\n"
            if not amateur_sorted:
                message += "В этой группе пока нет результатов.\n\n"
            else:
                for i, result in enumerate(amateur_sorted, 1):
                    _, username, best_series, total_tens, *_ = result
                    message += f"{i}. {username}: {best_series} очков, {total_tens}\n"

        # Send message to group
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=message)
        logger.info(f"Leaderboard published successfully to group {CHAT_ID}")
        
        # Reset the database for the next period
        reset_database()
        logger.info("Database reset for next period")
        
    except Exception as e:
        logger.error(f"Error publishing leaderboard: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(publish_leaderboard())
