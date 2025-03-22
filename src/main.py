import asyncio
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# Import your modules (make sure these exist in your project)
from database import create_database, add_user_result, get_user_result, validate_input, get_all_results
from utils import is_user_in_group
from config import BOT_TOKEN

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Check if message is from a group chat:
    - If bot is mentioned, respond with a message to use private chat
    - Otherwise silently ignore
    Returns True if the message is from a group chat (meaning it should be ignored).
    """
    try:
        if update.effective_chat and update.effective_chat.type in ['group', 'supergroup']:
            # Check if bot is mentioned in the message
            if update.message and update.message.text:
                bot_username = context.bot.username
                if f"@{bot_username}" in update.message.text:
                    logger.info(f"Bot mentioned in group chat by {update.message.from_user.username}")
                    # Reply only when mentioned
                    await update.message.reply_text(
                        f'@{update.message.from_user.username}, для внесения статистики и просмотра результатов, '
                        'пожалуйста, общайтесь со мной напрямую, чтобы не засорять общий чат.'
                    )
            
            # Always return True for group messages to prevent further processing
            return True
    except Exception as e:
        logger.error(f"Error in handle_group_message: {e}")
    
    return False  # Not a group message, proceed with normal handling

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the user issues /start."""
    if await handle_group_message(update, context):
        return
        
    user_id = update.message.from_user.id
    is_member, error_message = await is_user_in_group(user_id, context.bot)

    if not is_member:
        await update.message.reply_text(f'Для использования бота необходимо быть участником группы. {error_message}')
        return
        
    await update.message.reply_text(
        'Добро пожаловать в бот для результатов стрельбы!'
    )
    await help_command(update, context)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show a user’s currently saved result."""
    if await handle_group_message(update, context):
        return
        
    user_id = update.message.from_user.id
    result = get_user_result(user_id)
    if result:
        # result is a tuple of (user_id, username, best_series, central_tens, photo_id)
        await update.message.reply_text(
            f"Ваш текущий результат:\nЛучшая серия: {result[2]}, Количество центральных десяток: {result[3]}"
        )
    else:
        await update.message.reply_text("Вы еще не отправили никаких результатов.")

# Update the handle_result function to use the membership check
async def handle_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle a text message from the user containing best_series and central_tens.
    Example input: "99 7"
    """
    if await handle_group_message(update, context):
        return
        
    user_id = update.message.from_user.id

    # Validate user is in group
    is_member, error_message = await is_user_in_group(user_id, context.bot)

    if not is_member:
        await update.message.reply_text(f'Вам не разрешено отправлять результаты. {error_message}')
        return

    # Parse the incoming text
    text_parts = update.message.text.strip().split()
    if len(text_parts) < 2:
        await update.message.reply_text(
            'Пожалуйста, укажите и лучшую серию, и количество центральных десяток, например, "99 7"'
        )
        return

    try:
        best_series = int(text_parts[0])
        central_tens = int(text_parts[1])
    except ValueError:
        await update.message.reply_text(
            'Лучшая серия и количество центральных десяток должны быть числами.'
        )
        return

    # Validate input ranges
    if best_series < central_tens * 10:
        await update.message.reply_text(
            'Лучшая серия не может быть меньше, чем количество центральных десяток × 10.'
        )
        return

    if best_series > central_tens * 10 + (10 - central_tens) * 9:
        await update.message.reply_text(
            'Лучшая серия не может быть выше, чем количество центральных десяток × 10 и остальные выстрелы максимум по 9.'
        )
        return

    if not (0 <= best_series <= 100):
        await update.message.reply_text(
            'Лучшая серия должна быть числом от 0 до 100.'
        )
        return
        
    if not (0 <= central_tens <= 10):
        await update.message.reply_text(
            'Количество центральных десяток должно быть числом от 0 до 10.'
        )
        return

    # Validate and compare with previous results
    if validate_input(best_series, central_tens):
        previous_result = get_user_result(user_id)
        previous_group = None
        
        # Determine previous group if there was a previous result
        if previous_result:
            prev_best_series = previous_result[2]
            prev_central_tens = previous_result[3]
            
            # Determine the previous group
            if prev_best_series > 93:
                previous_group = "Профи"
            elif prev_best_series >= 80:
                previous_group = "Полупрофи"
            else:
                previous_group = "Любители"

            # If new results are worse, ignore them
            if best_series < prev_best_series or \
               (best_series == prev_best_series and central_tens < prev_central_tens):
                await update.message.reply_text(
                    'Ваши новые результаты не так хороши как предыдущие. Сохраняем старые результаты.'
                )
                return

        # Save the new result
        add_user_result(
            user_id,
            update.message.from_user.first_name,
            best_series,
            central_tens
        )
        
        # Determine the new group
        new_group = None
        if best_series > 93:
            new_group = "Профи"
        elif best_series >= 80:
            new_group = "Полупрофи"
        else:
            new_group = "Любители"
        
        # Check if user moved to a higher group
        if previous_result and previous_group != new_group:
            # Group upgrade hierarchy: Любители -> Полупрофи -> Профи
            if (previous_group == "Любители" and new_group in ["Полупрофи", "Профи"]) or \
               (previous_group == "Полупрофи" and new_group == "Профи"):
                # Send congratulation message
                await update.message.reply_text(
                    f'🎉 Поздравляем! 🎉\n'
                    f'Вы улучшили свой результат и перешли в группу "{new_group}"!\n'
                    f'Ваш новый результат: {best_series} очков, {central_tens}*.'
                )
                return
        
        # Regular success message if no group change
        await update.message.reply_text('Ваши результаты были записаны!')
    else:
        await update.message.reply_text(
            'Неверный ввод. Пожалуйста, убедитесь, что ваши результаты корректны.'
        )

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the current leaderboard of best results, filtered by user's skill group."""
    if await handle_group_message(update, context):
        return
        
    user_id = update.message.from_user.id
    user_result = get_user_result(user_id)
    
    results = get_all_results()
    
    if not results:
        await update.message.reply_text("Пока нет результатов для отображения.")
        return
    
    # Determine user's group
    user_group = "Любители"  # Default group if user has no results
    if user_result:
        best_series = user_result[2]
        if best_series > 93:
            user_group = "Профи"
        elif best_series >= 80:
            user_group = "Полупрофи"
        else:
            user_group = "Любители"
    
    # Filter results based on user's group
    if user_group == "Профи":
        filtered_results = [r for r in results if r[2] > 93]
        group_title = "🏆 Группа Профи 🏆"
    elif user_group == "Полупрофи":
        filtered_results = [r for r in results if 80 <= r[2] <= 93]
        group_title = "🏆 Группа Полупрофи 🏆"
    else:  # Любители
        filtered_results = [r for r in results if r[2] < 80]
        group_title = "🏆 Группа Любители 🏆"
    
    # Sort results by best_series (descending) and then by central_tens (descending)
    sorted_results = sorted(filtered_results, key=lambda x: (x[2], x[3]), reverse=True)
    
    # Format the leaderboard message
    leaderboard_text = f"{group_title}\n\n"
    
    if not sorted_results:
        leaderboard_text += "В этой группе пока нет результатов."
    else:
        for i, result in enumerate(sorted_results[:10], 1):  # Show top 10 results
            username = result[1]
            best_series = result[2]
            central_tens = result[3]
            leaderboard_text += f"{i}. {username}: {best_series} очков, {central_tens}*\n"
    
    await update.message.reply_text(leaderboard_text)

async def leaderboard_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display top 10 results for each of the three skill groups."""
    if await handle_group_message(update, context):
        return
        
    results = get_all_results()
    
    if not results:
        await update.message.reply_text("Пока нет результатов для отображения.")
        return
    
    # Filter results into three groups
    pro_results = [r for r in results if r[2] > 93]
    semi_pro_results = [r for r in results if 80 <= r[2] <= 93]
    amateur_results = [r for r in results if r[2] < 80]
    
    # Sort each group by best_series and central_tens
    pro_sorted = sorted(pro_results, key=lambda x: (x[2], x[3]), reverse=True)[:10]
    semi_pro_sorted = sorted(semi_pro_results, key=lambda x: (x[2], x[3]), reverse=True)[:10]
    amateur_sorted = sorted(amateur_results, key=lambda x: (x[2], x[3]), reverse=True)[:10]
    
    # Format the message
    leaderboard_text = "🏆 Таблица лидеров по всем группам 🏆\n\n"
    
    # Pro group
    leaderboard_text += "👑 Группа Профи 👑\n"
    if not pro_sorted:
        leaderboard_text += "В этой группе пока нет результатов.\n\n"
    else:
        for i, result in enumerate(pro_sorted, 1):
            username = result[1]
            best_series = result[2]
            central_tens = result[3]
            leaderboard_text += f"{i}. {username}: {best_series} очков, {central_tens}*\n"
        leaderboard_text += "\n"
    
    # Semi-pro group
    leaderboard_text += "🥈 Группа Полупрофи 🥈\n"
    if not semi_pro_sorted:
        leaderboard_text += "В этой группе пока нет результатов.\n\n"
    else:
        for i, result in enumerate(semi_pro_sorted, 1):
            username = result[1]
            best_series = result[2]
            central_tens = result[3]
            leaderboard_text += f"{i}. {username}: {best_series} очков, {central_tens}*\n"
        leaderboard_text += "\n"
    
    # Amateur group
    leaderboard_text += "🥉 Группа Любители 🥉\n"
    if not amateur_sorted:
        leaderboard_text += "В этой группе пока нет результатов.\n\n"
    else:
        for i, result in enumerate(amateur_sorted, 1):
            username = result[1]
            best_series = result[2]
            central_tens = result[3]
            leaderboard_text += f"{i}. {username}: {best_series} очков, {central_tens}*\n"
    
    await update.message.reply_text(leaderboard_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message when the user issues /help."""
    if await handle_group_message(update, context):
        return
        
    help_text = (
        "📋 Список команд бота:\n\n"
        "/status - Проверить ваш текущий результат\n"
        "/leaderboard - Посмотреть таблицу лидеров вашей группы\n"
        "/leaderboard_all - Посмотреть таблицу лидеров всех групп\n"
        "/help - Показать это сообщение\n\n"
        "Чтобы внести результаты стрельбы, просто отправьте два числа:\n"
        "Лучшая_серия    Количество_центральных_десяток\n"
        "Например: 99 7"
    )
    
    await update.message.reply_text(help_text)

async def main() -> None:
    """Set up the database, configure the bot, add handlers, and run polling."""
    # Initialize or create your database
    create_database()

    # Create the bot application
    application = Application.builder().token(BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("leaderboard_all", leaderboard_all))
    application.add_handler(CommandHandler("help", help_command))

    # Register a message handler (for the best_series / central_tens input)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_result)
    )

    # Removed scheduler code - will be handled by cron instead
    
    # Start the bot and run until user presses Ctrl-C
    await application.initialize()
    await application.start()
    
    try:
        await application.updater.start_polling()
        logger.info("Bot started and running...")
        # Keep the program running until user cancels
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("User initiated shutdown...")
    finally:
        logger.info("Shutting down...")
        await application.stop()
        await application.shutdown()
        logger.info("Bot has been shut down.")

if __name__ == "__main__":
    create_database()
    asyncio.run(main())
