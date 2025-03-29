import asyncio
import logging
import os
# Removed unused import: sqlite3
# Removed unused import: datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)
# Fix the incorrect import for command scopes
from telegram import BotCommandScopeDefault, BotCommandScopeAllGroupChats

# Import from the refactored database package
from database import (
    # Removed duplicate import: init_consent_db
    create_database,
    add_user_result,
    get_user_result,
    validate_input,
    # Removed unused import: get_all_results
)
# Import from the new user module
from user import (
    is_user_in_group,
    init_consent_db,
    save_user_consent,
    check_user_consent,
    revoke_user_consent,
    handle_group_message,  # Updated to import from user module
    leaderboard,
    leaderboard_all,  # Import leaderboard functions from user package
    # Add these imports for admin functionality
    register_admin_handlers
)
# Remove this import as it's now included in the user package
# from leaderboard import leaderboard, leaderboard_all
from config import BOT_TOKEN

# Get data directory from environment variable or use default
DATA_DIR = os.environ.get('DATA_DIR', './data')

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants - use environment-based path
CONSENT_DB = os.path.join(DATA_DIR, 'consent.db')

# Help text constant to avoid duplication
HELP_TEXT = (
    "📋 Список команд бота:\n\n"
    "/status - Проверить ваш текущий результат\n"
    "/leaderboard - Посмотреть таблицу лидеров вашей группы\n"
    "/leaderboard_all - Посмотреть таблицу лидеров всех групп\n"
    "/revoke - Отозвать согласие на обработку данных\n"
    "/help - Показать это сообщение\n\n"
    "Чтобы внести результаты стрельбы, просто отправьте два числа:\n"
    "Серия КоличествоДесяток(центровых, если серия >=93)\n"
    "Например: 92 3"
)

# Consent required message to avoid duplication
CONSENT_REQUIRED_TEXT = (
    "Хочу убедиться, что всё по-честному и безопасно для тебя 😊 "
    "Для отправки результатов нужно согласие на обработку данных. "
    "Пожалуйста, нажми /start и прими условия соглашения, когда будешь готов. Я подожду 🤝"
)

def get_consent_keyboard():
    """Return the standard consent keyboard with three options."""
    keyboard = [
        [InlineKeyboardButton("✅ Согласен", callback_data='agree')],
        [InlineKeyboardButton("📋 Просмотреть политику обработки данных", callback_data='view_policy')],
        [InlineKeyboardButton("❌ Не согласен", callback_data='disagree')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==== CONSENT HANDLERS ====
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message and request user consent if not already given."""
    if await handle_group_message(update, context):
        return
        
    user = update.effective_user
    
    # Check consent first
    if check_user_consent(user.id):
        logger.info(f"User {user.username} (ID: {user.id}) already gave consent, proceeding")
        await update.message.reply_text(f"С возвращением, {user.first_name}! 👋\nСогласие на обработку персональных данных уже получено — первый выстрел сделан. Можем продолжать.")
        
        # Check group membership
        user_id = update.message.from_user.id
        is_member, error_message = await is_user_in_group(user_id, context.bot)

        if not is_member:
            await update.message.reply_text(f'Для использования бота необходимо быть участником группы. {error_message}')
            return
            
        await help_command(update, context)
        return

    # Request consent if not given
    reply_markup = get_consent_keyboard()

    text = (
        "Привет, стрелок! 👋\n\n"
        "Прежде чем выйти на рубеж — один важный шаг. Ознакомься с пользовательским соглашением.\n"
        "Мы сохраняем результаты твоей стрельбы — только по минимуму и исключительно ради честной статистики. 📊🔐\n\n"
        "Нажимая кнопку ниже, ты подтверждаешь своё согласие с условиями.\n"
        "С этого момента — ты в игре. Заряжай... Старт! 💥🎯"
            )

    await update.message.reply_text(text, reply_markup=reply_markup)
    logger.info(f"Consent request sent to user {user.username} (ID: {user.id})")

async def handle_consent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the user's consent choice from inline keyboard."""
    query = update.callback_query
    user = query.from_user
    await query.answer()

    if query.data == 'agree':
        success = save_user_consent(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name
        )
        
        if success:
            await query.edit_message_text(
                "Есть контакт! 🎉 Спасибо за согласие — выстрел в десятку! 🎯\n\n"
                "Теперь всё готово: рубеж открыт, мишени ждут, команда болеет за тебя! 🚀\n"
                "Вперёд к победам и ярким результатам! 🥇💪"
            )
            
            # Check group membership after consent
            is_member, error_message = await is_user_in_group(user.id, context.bot)
            if not is_member:
                await context.bot.send_message(
                    chat_id=user.id,
                    text=f'Для использования бота необходимо быть участником группы. {error_message}'
                )
            else:
                # Send help message using the constant
                await context.bot.send_message(chat_id=user.id, text=HELP_TEXT)
        else:
            await query.edit_message_text("Произошла ошибка при сохранении согласия. Пожалуйста, попробуйте позже.")
    
    elif query.data == 'disagree':
        await query.edit_message_text(
            "Понял тебя. Без согласия дальше идти нельзя — такие правила на рубеже. 😔\n"
            "Если передумаешь — команда и мишени будут ждать. 🎯"
        )
        logger.info(f"User {user.username} (ID: {user.id}) has declined consent")
    
    elif query.data == 'view_policy':
        try:
            # Get the policy file path from root directory
            policy_path = 'policy.pdf'
            
            # Edit the current message to inform the user
            await query.edit_message_text("Отправляю файл политики обработки данных...")
            
            # Send the policy file as a document
            await context.bot.send_document(
                chat_id=user.id,
                document=open(policy_path, 'rb'),
                filename="Политика обработки данных.pdf",
                caption="Политика обработки персональных данных"
            )
            logger.info(f"Policy document sent to user {user.username} (ID: {user.id})")
            
            # Show the consent options again in a new message
            reply_markup = get_consent_keyboard()
            
            text = "Пожалуйста, подтвердите своё согласие с политикой обработки персональных данных:"
            await context.bot.send_message(
                chat_id=user.id,
                text=text,
                reply_markup=reply_markup
            )
            
        except FileNotFoundError:
            logger.error(f"Policy file not found at {policy_path}")
            await query.edit_message_text(
                "Извините, файл политики обработки данных не найден. Пожалуйста, обратитесь к администратору."
            )
            
            # Re-display consent buttons
            reply_markup = get_consent_keyboard()
            await context.bot.send_message(
                chat_id=user.id,
                text="Пожалуйста, выберите один из вариантов:",
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Error sending policy to user {user.id}: {e}")
            await query.edit_message_text(
                "Извините, произошла ошибка при отправке политики. Пожалуйста, попробуйте позже."
            )
            
            # Re-display consent buttons
            reply_markup = get_consent_keyboard()
            await context.bot.send_message(
                chat_id=user.id,
                text="Пожалуйста, выберите один из вариантов:",
                reply_markup=reply_markup
            )

async def revoke_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Revoke user's consent."""
    if await handle_group_message(update, context):
        return
        
    user = update.effective_user
    if not check_user_consent(user.id):
        await update.message.reply_text("Ты ещё не давал согласие или уже его отозвал.")
        return

    success = revoke_user_consent(user.id)
    if success:
        await update.message.reply_text(
            "Ты сделал свой выбор — спокойно, сосредоточенно, как перед последним выстрелом в финале. "
            "Но запомни: настоящий стрелок никогда не теряет хватку. Он просто уходит с рубежа, чтобы вернуться сильнее.\n\n"
            "Когда почувствуешь, что дыхание ровное, хват уверенный и снова хочется в бой — просто напиши /start. "
            "Мишень ждет. А ты уже знаешь, как это — бить точно в центр. 🎯🥇"
)
        logger.info(f"User {user.username} (ID: {user.id}) has revoked consent")
    else:
        await update.message.reply_text("Произошла ошибка при отзыве согласия. Пожалуйста, попробуйте позже.")

def extract_shooting_data(result):
    """Extract best series and total tens from a result tuple.
    
    Args:
        result: A tuple containing user shooting data
        
    Returns:
        Tuple of (best_series, total_tens)
    """
    if not result:
        return None, None
    
    best_series = result[4]
    total_tens = result[5]
    return best_series, total_tens

# Update existing handlers to check for consent
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show a user's currently saved result."""
    if await handle_group_message(update, context):
        return
        
    user_id = update.message.from_user.id
    
    # Check consent first
    if not check_user_consent(user_id):
        await update.message.reply_text(
            "Перед выходом на линию нужен чёткий сигнал согласия. 📝\n"
            "Без этого — ни одного выстрела.\n\n"
            "Готов продолжить? Используй команду /start и возвращайся на рубеж. 🎯"
        )
        return
    
    # Get user result and extract data using the helper function
    result = get_user_result(user_id)
    if result:
        best_series, total_tens = extract_shooting_data(result)
        if best_series >= 93:
            message = f"Ваш текущий результат:\nЛучшая серия: {best_series}, количество центральных десяток: {total_tens}x"
        else:
            message = f"Ваш текущий результат:\nЛучшая серия: {best_series}, количество десяток: {total_tens}"
        
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("Вы еще не отправили никаких результатов.")

# Update the handle_result function to use the membership check
async def handle_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle a text message from the user containing best_series and total_tens.
    Example input: "92 3"
    """
    # First check if we have a valid message with a user
    if not update.message or not update.message.from_user:
        logger.warning("Received update without valid message or user information")
        return
        
    if await handle_group_message(update, context):
        return
        
    user_id = update.message.from_user.id
    
    # Check if user has given consent
    if not check_user_consent(user_id):
        await update.message.reply_text(CONSENT_REQUIRED_TEXT)
        return

    # Validate user is in group
    is_member, error_message = await is_user_in_group(user_id, context.bot)

    if not is_member:
        await update.message.reply_text(f'Вам не разрешено отправлять результаты. {error_message}')
        return

    # Parse the incoming text
    text_parts = update.message.text.strip().split()
    if len(text_parts) < 2:
        await update.message.reply_text(
            'Пожалуйста, укажите и лучшую серию, и количество десяток, например, "92 3"'
        )
        return

    try:
        best_series = int(text_parts[0])
        total_tens = int(text_parts[1])
    except ValueError:
        await update.message.reply_text(
            'Чтобы всё сработало как надо, "лучшая серия" и "количество десяток" нужно ввести цифрами 😊.'
        )
        return

    # Validate input ranges
    if best_series < 93:
        if best_series < total_tens * 10:
            await update.message.reply_text(
                'Ой, кажется, тут небольшая путаница: Лучшая серия должна быть не меньше, чем количество десяток × 10. Давай перепроверим! 😊'
            )
            return

        if best_series > total_tens * 10 + (10 - total_tens) * 9:
            await update.message.reply_text(
                'Похоже, "Лучшая серия" завышена 😊 Она не может быть больше, чем количество десяток × 10, даже если остальные выстрелы — девятки. Проверь, пожалуйста!'
            )
            return

    if not (0 <= best_series <= 100):
        await update.message.reply_text(
            'Хм, кажется, с серией что-то не так 🤔 Она должна быть числом от 0 до 100. Проверь ещё разок, пожалуйста! 😊'
        )
        return
        
    if not (0 <= total_tens <= 10):
        await update.message.reply_text(
            'Проверь, пожалуйста: количество десяток должно быть числом от 0 до 10 😊.'
        )
        return

    # Validate and compare with previous results
    if validate_input(best_series, total_tens):
        previous_result = get_user_result(user_id)
        previous_group = None
        
        # Determine previous group if there was a previous result
        if previous_result:
            prev_best_series = previous_result[4]  # Updated index for best_series
            prev_total_tens = previous_result[5]   # Updated index for total_tens
            
            # Determine the previous group
            if prev_best_series >= 93:
                previous_group = "Профи"
            elif prev_best_series >= 80:
                previous_group = "Продвинутые"
            else:
                previous_group = "Любители"

            # If new results are worse, ignore them
            if best_series < prev_best_series or \
               (best_series == prev_best_series and total_tens < prev_total_tens):
                await update.message.reply_text(
                    'Пока оставим старые результаты — новые чуть скромнее. Но это всего лишь шаг в пути 💫 Не останавливайся, ты растёшь с каждым выстрелом!'
                )
                return

        # Get user details from Telegram
        first_name = update.message.from_user.first_name
        last_name = update.message.from_user.last_name or ""
        username = update.message.from_user.username or ""

        # Save the new result with separated user fields
        add_user_result(
            user_id,
            first_name,
            last_name,
            username,
            best_series,
            total_tens
        )
        
        # Determine the new group
        new_group = None
        if best_series >= 93:
            new_group = "Профи"
        elif best_series >= 80:
            new_group = "Продвинутые"
        else:
            new_group = "Любители"
        
        # Check if user moved to a higher group
        if previous_result and previous_group != new_group:
            # Group upgrade hierarchy: Любители -> Продвинутые -> Профи
            if (previous_group == "Любители" and new_group in ["Продвинутые", "Профи"]) or \
               (previous_group == "Продвинутые" and new_group == "Профи"):
                # Send congratulation message
                await update.message.reply_text(
                    f'🏆 Отличная серия, {update.effective_user.first_name}! 🏆\n'
                    f'Ты поднялся на новый уровень и теперь в группе **"{new_group}"**!\n'
                    f'Твой результат: {best_series}, {total_tens} — уверенное попадание в прогресс! 🎯'
                )
                return

        # Regular success message if no group change
        await update.message.reply_text('Есть! Вот это выстрел… Душа радуется. ❤️‍🔥🎯')
    else:
        await update.message.reply_text(
            'Хм, система немножко запуталась 😅 Проверь, пожалуйста, чтобы всё было по-честному — и погнали дальше!'
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message when the user issues /help."""
    if await handle_group_message(update, context):
        return
        
    await update.message.reply_text(HELP_TEXT)

async def handle_unsupported_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unsupported content types like photos, files or voice messages."""
    if await handle_group_message(update, context):
        return
        
    user_id = update.message.from_user.id
    
    # Check if user has given consent
    if not check_user_consent(user_id):
        await update.message.reply_text(CONSENT_REQUIRED_TEXT)
        return
        
    await update.message.reply_text(
        "Ой! Пока что я не умею работать с фото, файлами и голосовыми сообщениями 🙈\n"
        "Но ничего, это временно — обязательно научусь!\n"
        "А сейчас просто напиши результат в текстовом виде, например: 92 3 ✍️🙂"
        )

# Update the main function to initialize consent DB and add new handlers
async def main() -> None:
    """Set up the database, configure the bot, add handlers, and run polling."""
    # Initialize databases - pass the data directory where needed
    create_database()  # Remove the DATA_DIR parameter
    init_consent_db()

    # Create the bot application
    application = Application.builder().token(BOT_TOKEN).build()

    # Set up bot commands for the menu button
    private_commands = [
        # BotCommand("start", "Начать использование бота"),  # Removed from menu
        BotCommand("status", "Проверить ваш текущий результат"),
        BotCommand("leaderboard", "Таблица лидеров вашей группы"),
        BotCommand("leaderboard_all", "Таблица лидеров всех групп"),
        BotCommand("revoke", "Отозвать согласие на обработку данных"),
        BotCommand("help", "Показать список команд")
    ]
    
    # Set commands for private chats only
    await application.bot.set_my_commands(
        commands=private_commands,
        scope=BotCommandScopeDefault()
    )
    
    # Remove commands from group chats by setting an empty list
    await application.bot.set_my_commands(
        commands=[],  # empty command list
        scope=BotCommandScopeAllGroupChats()
    )
    
    logger.info("Bot menu commands have been set up for private chats only")

    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))  # Use new consent-aware start handler
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("leaderboard_all", leaderboard_all))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("revoke", revoke_command))  # Add the revoke command handler
    
    # Register admin handlers
    register_admin_handlers(application)
    
    # Add callback query handler for consent buttons
    application.add_handler(CallbackQueryHandler(handle_consent))

    # Handle unsupported content types (photos, files, voice messages)
    application.add_handler(
# Вместо filters.MEDIA:
        MessageHandler(
            filters.ATTACHMENT | filters.CONTACT | filters.LOCATION,
            handle_unsupported_content
        )
    )
    
    # Register a message handler (for the best_series / total_tens input)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_result)
    )

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
    create_database()  # Remove the DATA_DIR parameter
    asyncio.run(main())
