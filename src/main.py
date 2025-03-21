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
        if previous_result:
            prev_best_series = previous_result[2]
            prev_central_tens = previous_result[3]

            # If new results are worse, ignore them
            if best_series < prev_best_series or \
               (best_series == prev_best_series and central_tens < prev_central_tens):
                await update.message.reply_text(
                    'Ваши новые результаты не так хороши как предыдущие. Сохраняем старые результаты.'
                )
                return

        add_user_result(
            user_id,
            update.message.from_user.first_name,
            best_series,
            central_tens
        )
        await update.message.reply_text('Ваши результаты были записаны!')
    else:
        await update.message.reply_text(
            'Неверный ввод. Пожалуйста, убедитесь, что ваши результаты корректны.'
        )

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display the current leaderboard of best results."""
    if await handle_group_message(update, context):
        return
        
    results = get_all_results()
    
    if not results:
        await update.message.reply_text("Пока нет результатов для отображения.")
        return
    
    # Sort results by best_series (descending) and then by central_tens (descending)
    sorted_results = sorted(results, key=lambda x: (x[2], x[3]), reverse=True)
    
    # Format the leaderboard message
    leaderboard_text = "🏆 Таблица лидеров 🏆\n\n"
    for i, result in enumerate(sorted_results[:10], 1):  # Show top 10 results
        username = result[1]
        best_series = result[2]
        central_tens = result[3]
        leaderboard_text += f"{i}. {username}: {best_series} очков, {central_tens} центральных десяток\n"
    
    await update.message.reply_text(leaderboard_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message when the user issues /help."""
    if await handle_group_message(update, context):
        return
        
    help_text = (
        "📋 Список команд бота:\n\n"
        "/status - Проверить ваш текущий результат\n"
        "/leaderboard - Посмотреть таблицу лидеров\n"
        "/help - Показать это сообщение\n\n"
        "Чтобы внести результаты стрельбы, просто отправьте два числа:\n"
        "лучшая_серия количество_центральных_десяток\n"
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
