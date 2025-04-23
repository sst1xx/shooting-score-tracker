import logging
import os
import asyncio
import re
import random  # Import the random module
from telegram import Bot
from telegram.error import TelegramError
from database import get_all_results, create_database, format_display_name
from database.consent_db import get_all_child_user_ids  # Import the function to get child user IDs
from config import BOT_TOKEN, CHAT_ID, DB_PATH
from datetime import datetime

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# List of congratulatory messages
CONGRATULATORY_MESSAGES = [
    "💫 Великолепные волшебники точности! Каждый ваш выстрел приближает к новым высотам. Вперёд, к новым достижениям! ✨",
    "🥳 Ура, друзья! Сезон завершён, но впереди — бескрайние горизонты доброты и успеха. 🦸‍♀️🦸‍♂️ Спасибо за ваши сердца, бьющееся в унисон!",
    "🎉 Смелые друзья, ваш упорный труд и страсть к победе освещают путь вперёд. Дерзайте и не останавливайтесь! 💪",
    "🎈 С окончанием сезона, друзья! Ваши меткие выстрелы и тёплые улыбки — бесценны. 🍀 В новом сезоне пусть вас согревает поддержка близких.",
    "✨ Вы — наши звёзды, освещающие путь теплом и радостью. 🌟 Спасибо за вашу энергию. Новый сезон принесёт ещё больше волшебства!",
    "🏆 Дорогие участники, вы дарите нам любовь к спорту и жизни. 💪 Пусть новый сезон будет наполнен счастливыми мгновениями и уютом!",
    "🚀 Вы способны на большее! Каждый ваш успех — доказательство силы воли и упорства. Не останавливайтесь!",
    "✨ Дорогие друзья, вы — наше вдохновение и поддержка. Ваше тепло и энтузиазм наполняют нас радостью. 🧡 Новый сезон встретим вместе, он обещает быть волшебным! 🌿",
    "🔥 Дерзайте, стрелки! Каждый выстрел — шаг к новым вершинам. Вера в себя движет вперёд!",
    "🌟 Отважные стрелки, ваши успехи вселяют смелость и настрой на победы! Вы на верном пути, и впереди — только новые вершины! 🚀",
    "💯 Вы — сердце нашего тира. Ваша страсть и доброта объединяют нас всех! 🥇 Пусть впереди будет только радость и вдохновение.",
    "❤️ Помните, вы не одни: мы всегда рядом, чтобы поддержать и вдохновить. Пусть новый сезон согревает вас любовью!",
    "🌠 Ваши достижения — уютный очаг вдохновения для всех нас. Благодарим за ваш позитив и поддержку! 🤩 Новый сезон принесёт ещё больше тёплых моментов.",
    "🎇 Ваши результаты — словно салют тёплых чувств! 🌌 Спасибо за каждый момент вместе. Новый сезон — новая глава нашего дружного приключения.",
    "🎉 Поздравляем всех с яркими результатами! 🎯 Ваше участие и дружба — самое ценное. Пусть новый сезон наполнится теплыми моментами и вдохновением!",
    "💖 Ваше участие и вера в себя — самый тёплый подарок. Вы делаете наш мир светлее! 🙏 Пусть новый сезон наполнится яркими огоньками успеха.",
    "🌸 Ваши улыбки и дружеская поддержка — самая тёплая награда. В новом сезоне пусть будет много светлых моментов!",
    "🎊 Дорогие друзья, ваша сплочённость и талант делают атмосферу особенной. 🙌 Спасибо, что вы с нами. Впереди — новые свершения и победные обнимашки!",
    "🍂 Ощутите уют каждого мгновения: ваши успехи — это семейное дело, и мы гордимимся каждым из вас. Тепла и вдохновения!",
    "🥳 От всего сердца поздравляем наших героев! Ваше старание и забота друг о друге создают настоящую атмосферу дома. 🏅 Пусть новый сезон будет наполнен любовью и радостью!"
]


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
    """Backup the old database with timestamp and create a new one."""
    try:
        # Use the centralized database path from config
        if os.path.exists(DB_PATH):
            # Create a timestamp in format YYYY-MM-DD
            timestamp = datetime.now().strftime('%Y-%m-%d')
            
            # Generate backup filename with timestamp
            db_name = os.path.basename(DB_PATH)
            db_dir = os.path.dirname(DB_PATH)
            backup_filename = f"{db_name.split('.')[0]}_{timestamp}.db"
            backup_path = os.path.join(db_dir, backup_filename)
            
            # Rename the old database file instead of deleting it
            os.rename(DB_PATH, backup_path)
            logger.info(f"Old database backed up to: {backup_path}")
        
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
        
        # Get all child user IDs first
        child_user_ids = get_all_child_user_ids()
        
        # Filter results into four groups (including children)
        pro_results = [r for r in results if r[4] >= 93 and r[0] not in child_user_ids]  # Best series at index 4
        semi_pro_results = [r for r in results if 80 <= r[4] <= 92 and r[0] not in child_user_ids]
        amateur_results = [r for r in results if r[4] <= 79 and r[0] not in child_user_ids]
        child_results = [r for r in results if r[0] in child_user_ids]  # Using child_user_ids instead of r[6]
        
        # Sort each group by best_series and total_tens
        pro_sorted = sorted(pro_results, key=lambda x: (x[4], x[5]), reverse=True)
        semi_pro_sorted = sorted(semi_pro_results, key=lambda x: (x[4], x[5]), reverse=True)
        amateur_sorted = sorted(amateur_results, key=lambda x: (x[4], x[5]), reverse=True)
        child_sorted = sorted(child_results, key=lambda x: (x[4], x[5]), reverse=True)
        
        # Create message
        message = "🏅 Наши победители 🏅\n\n"
        
        # Check if any group has participants
        if not (pro_sorted or semi_pro_sorted or amateur_sorted or child_sorted):
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
            if child_sorted:
                _, first_name, last_name, username, score, tens = child_sorted[0]
                winner = format_display_name(first_name, last_name)
                username_display = f" (@{username})" if username else ""
                message += f"🌟 Дети: {winner}{username_display} {score}-{tens}\n"
        
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
            message += "\n"
        
        # Children group (new)
        message += "🌟 Группа Дети 🌟\n"
        if not child_sorted:
            message += "В этой группе пока нет результатов.\n\n"
        else:
            for i, result in enumerate(child_sorted, 1):
                _, first_name, last_name, _, best_series, total_tens = result
                display_name = format_display_name(first_name, last_name)
                message += f"{i}. {display_name}: {best_series}-{total_tens}\n"
            message += "\n"
            
        # Select a random congratulatory message
        random_congrats = random.choice(CONGRATULATORY_MESSAGES)
        message += f"{random_congrats}\n"
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
