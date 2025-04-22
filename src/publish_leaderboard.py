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
    "✨ Друзья, вы — просто невероятные! Поздравляем от всего сердца! Столько тепла, старания и душевности в каждом шаге — гордимся вами до мурашек. 🧡 Новый сезон — как чистый лист, а вы уже держите в руках самые яркие краски. Пусть впереди будет только светлое и своё. 🌿",
    "🌟 Поздравляем всех участников! Ваши результаты — это огонь! 🔥 Каждый выстрел — шаг к мастерству. Новый сезон уже ждёт ваших новых рекордов! Вперёд, к звёздам! 🚀",
    "🎉 Браво, стрелки! Вы показали класс! 💪 Спасибо за азарт, точность и дружескую атмосферу. Пусть следующий сезон принесёт ещё больше побед и радости! 🏆",
    "💫 Какие же вы молодцы! Ваши успехи вдохновляют! ✨ Спасибо за участие и волю к победе. Впереди новый сезон — новые цели и достижения! Не сбавляйте темп! 🎯",
    "🥳 Поздравляем победителей и всех участников! Вы — настоящие герои нашего тира! 🏅 Спасибо за вашу страсть и меткость. Новый сезон — новая страница вашей истории успеха! 📖",
    "🌠 Фантастические результаты! Вы превзошли все ожидания! 🤩 Спасибо за яркие эмоции и спортивный дух. Пусть новый сезон будет таким же успешным и захватывающим! 💥",
    "🎊 Отличная работа, команда! Ваши достижения — наша гордость! 🙌 Спасибо за упорство и мастерство. Впереди новый сезон — время ставить новые рекорды! 📈",
    "💖 Сердечно поздравляем всех! Вы показали невероятную меткость и выдержку! 🙏 Спасибо за ваше участие и позитив. Новый сезон — новые возможности! Дерзайте! ✨",
    "💯 Вы — лучшие! Ваши результаты говорят сами за себя! 🥇 Спасибо за вашу преданность спорту и стремление к совершенству. Пусть новый сезон станет ещё ярче! 🌟",
    "🎈 Поздравляем с завершением сезона! Вы все — большие молодцы! 🥳 Спасибо за азарт, улыбки и меткие выстрелы. Впереди новый сезон — пусть он будет полон удачи! 🍀",
    "🎇 Вау! Это было незабываемо! Ваши результаты — просто космос! 🌌 Спасибо за драйв и мастерство. Новый сезон обещает быть ещё интереснее! Готовы? 😉",
    "🏆 Поздравляем чемпионов и всех, кто принял участие! Вы — сила! 💪 Спасибо за честную борьбу и спортивный характер. Новый сезон — новые вызовы! Принимаете? 🔥",
    "✨ Вы — настоящие звёзды стрельбы! Ваши успехи сияют ярко! 🌟 Спасибо за вашу энергию и точность. Пусть новый сезон принесёт вам ещё больше блестящих побед! 💎",
    "🥳 Ура! Сезон завершён на высокой ноте! Вы все — супер! 🦸‍♀️🦸‍♂️ Спасибо за ваше мастерство и командный дух. Впереди новый сезон — время новых свершений! 🚀",
    "🎉 Поздравляем всех стрелков! Вы показали невероятные результаты! 🎯 Спасибо за вашу страсть к стрельбе и волю к победе. Новый сезон — новые горизонты! Покоряйте их! 🗺️"
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
