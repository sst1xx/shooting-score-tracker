import logging
import os
import asyncio
import re
from telegram import Bot
from telegram.error import TelegramError
from database import get_all_results, create_database, format_display_name
from config import BOT_TOKEN, CHAT_ID, DB_PATH

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def parse_chat_ids(chat_id_config):
    """Parse CHAT_ID string into a list of chat IDs."""
    if not chat_id_config:
        return []
    
    if not isinstance(chat_id_config, str):
        return [str(chat_id_config)]
    
    # Split by comma, semicolon, or space
    ids = re.split(r'[,;\s]+', chat_id_config.strip())
    return [id.strip() for id in ids if id.strip()]

def reset_database():
    """Delete the old database and create a new one."""
    try:
        # Use the centralized database path from config
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            logger.info(f"Old database deleted: {DB_PATH}")
        
        # Create a new database using the function from database module
        create_database()
        logger.info("New database initialized")
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        raise

async def publish_leaderboard():
    """Publish leaderboard to all group chats and reset the database."""
    try:
        # Get all results from the database
        results = get_all_results()
        
        if not results:
            logger.info("No results found. Skipping leaderboard publication.")
            return  # Early return - don't send any messages
        
        # Create bot instance
        bot = Bot(token=BOT_TOKEN)
        
        # Get bot information to use the real username
        bot_info = await bot.get_me()
        bot_username = f"@{bot_info.username}" if bot_info.username else ""
        
        # Filter results into three groups
        pro_results = [r for r in results if r[4] >= 93]  # Updated index for best_series
        semi_pro_results = [r for r in results if 80 <= r[4] <= 92]  # Updated index for best_series
        amateur_results = [r for r in results if r[4] <= 79]  # Updated index for best_series
        
        # Sort each group by best_series and total_tens
        pro_sorted = sorted(pro_results, key=lambda x: (x[4], x[5]), reverse=True)[:10]  # Updated indexes
        semi_pro_sorted = sorted(semi_pro_results, key=lambda x: (x[4], x[5]), reverse=True)[:10]  # Updated indexes
        amateur_sorted = sorted(amateur_results, key=lambda x: (x[4], x[5]), reverse=True)[:10]  # Updated indexes
        
        # Create message
        message = "🏅 Наши победители 🏅\n\n"
        
        # Check if any group has participants
        if not (pro_sorted or semi_pro_sorted or amateur_sorted):
            message += "Пока нет участников ни в одной группе.\n"
        else:
            if pro_sorted:
                _, first_name, last_name, username, score, tens = pro_sorted[0]
                winner = format_display_name(first_name, last_name)
                username_display = f" (@{username})" if username else ""
                message += f"👑 Профи: {winner}{username_display} {score}-{tens}x\n"
            if semi_pro_sorted:
                _, first_name, last_name, username, score, tens = semi_pro_sorted[0]
                winner = format_display_name(first_name, last_name)
                username_display = f" (@{username})" if username else ""
                message += f"🥈 Продвинутые: {winner}{username_display} {score}-{tens}\n"
            if amateur_sorted:
                _, first_name, last_name, username, score, tens = amateur_sorted[0]
                winner = format_display_name(first_name, last_name)
                username_display = f" (@{username})" if username else ""
                message += f"🥉 Любители: {winner}{username_display} {score}-{tens}\n"
        
        # Now show the detailed leaderboard tables
        message += "\n📊 Подробная таблица 📊\n\n"
        
        # Pro group
        message += "👑 Группа Профи 👑\n"
        if not pro_sorted:
            message += "В этой группе пока нет результатов.\n\n"
        else:
            for i, result in enumerate(pro_sorted, 1):
                _, first_name, last_name, _, best_series, total_tens = result
                display_name = format_display_name(first_name, last_name)
                message += f"{i}. {display_name}: {best_series}-{total_tens}x\n"
            message += "\n"
        
        # Semi-pro group
        message += "🥈 Группа Продвинутые 🥈\n"
        if not semi_pro_sorted:
            message += "В этой группе пока нет результатов.\n\n"
        else:
            for i, result in enumerate(semi_pro_sorted, 1):
                _, first_name, last_name, _, best_series, total_tens = result
                display_name = format_display_name(first_name, last_name)
                message += f"{i}. {display_name}: {best_series}-{total_tens}\n"
            message += "\n"
        
        # Amateur group
        message += "🥉 Группа Любители 🥉\n"
        if not amateur_sorted:
            message += "В этой группе пока нет результатов.\n\n"
        else:
            for i, result in enumerate(amateur_sorted, 1):
                _, first_name, last_name, _, best_series, total_tens = result
                display_name = format_display_name(first_name, last_name)
                message += f"{i}. {display_name}: {best_series}-{total_tens}\n"
            
        # Add congratulatory message at the end
        message += "\n✨ Друзья, вы — просто невероятные. Поздравляем от всего сердца! Столько тепла, старания и душевности в каждом шаге — гордимся вами до мурашек. 🧡 Новый сезон — как чистый лист, а вы уже держите в руках самые яркие краски. Пусть впереди будет только светлое и своё. 🌿\n"
        message += f"\nОбнимаем мысленно и всегда рядом — ваш {bot_username} ☕️🧸"


        # Parse CHAT_ID to get multiple group IDs
        chat_ids = parse_chat_ids(CHAT_ID)
        
        if not chat_ids:
            logger.error("No valid chat IDs found in configuration")
            return
            
        logger.info(f"Attempting to publish leaderboard to {len(chat_ids)} groups: {chat_ids}")
        
        # Send message to each group
        success_count = 0
        for chat_id in chat_ids:
            try:
                chat_id_int = int(chat_id)
                await bot.send_message(chat_id=chat_id_int, text=message)
                logger.info(f"Leaderboard published successfully to group {chat_id}")
                success_count += 1
            except TelegramError as e:
                logger.error(f"Failed to send leaderboard to group {chat_id}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error sending to group {chat_id}: {e}")
        
        if success_count > 0:
            # Reset the database for the next period only if at least one publish was successful
            reset_database()  # Using our new function that handles complete reset
            logger.info("Database reset for next period")
        else:
            logger.error("Failed to publish leaderboard to any group. Database not reset.")
        
    except Exception as e:
        logger.error(f"Error in publish_leaderboard: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(publish_leaderboard())
