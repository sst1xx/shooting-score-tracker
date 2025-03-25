import asyncio
import logging
import os
import sqlite3
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

# Import from the refactored database package
from database import (
    init_consent_db,
    create_database,
    add_user_result,
    get_user_result,
    validate_input,
    get_all_results
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
    leaderboard_all  # Import leaderboard functions from user package
)
# Remove this import as it's now included in the user package
# from leaderboard import leaderboard, leaderboard_all
from config import BOT_TOKEN

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
CONSENT_DB = os.path.join('data', 'consent.db')

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
            # Get the policy file path
            policy_path = os.path.join(os.path.dirname(__file__), '..', 'policy.md')
            
            # Edit the current message to inform the user
            await query.edit_message_text("Отправляю файл политики обработки данных...")
            
            # Send the policy file as a document
            await context.bot.send_document(
                chat_id=user.id,
                document=open(policy_path, 'rb'),
                filename="Политика обработки данных.md",
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
            "Мишени ждут. Команда готова. А ты уже знаешь, как это — бить точно в центр. 🎯🥇"
)
        logger.info(f"User {user.username} (ID: {user.id}) has revoked consent")
    else:
        await update.message.reply_text("Произошла ошибка при отзыве согласия. Пожалуйста, попробуйте позже.")

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
    
    # Existing code continues...
    result = get_user_result(user_id)
    if result:
        # result is a tuple of (user_id, username, best_series, total_tens, photo_id)
        if result[2] >= 93:
            message = f"Ваш текущий результат:\nЛучшая серия: {result[2]}, количество центральных десяток: {result[3]}x"
        else:
            message = f"Ваш текущий результат:\nЛучшая серия: {result[2]}, количество десяток: {result[3]}"
        
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("Вы еще не отправили никаких результатов.")

# Update the handle_result function to use the membership check
async def handle_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle a text message from the user containing best_series and total_tens.
    Example input: "92 3"
    """
    if await handle_group_message(update, context):
        return
        
    user_id = update.message.from_user.id
    
    # Check if user has given consent
    if not check_user_consent(user_id):
        await update.message.reply_text(
            "Для отправки результатов необходимо дать согласие на обработку данных. "
            "Пожалуйста, используйте команду /start и примите условия соглашения."
        )
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
            'Лучшая серия и количество десяток должны быть числами.'
        )
        return

    # Validate input ranges
    if best_series < 93:
        if best_series < total_tens * 10:
            await update.message.reply_text(
                'Лучшая серия не может быть меньше, чем количество десяток × 10.'
            )
            return

        if best_series > total_tens * 10 + (10 - total_tens) * 9:
            await update.message.reply_text(
                'Лучшая серия не может быть выше, чем количество десяток × 10 и остальные выстрелы максимум по 9.'
            )
            return

    if not (0 <= best_series <= 100):
        await update.message.reply_text(
            'Лучшая серия должна быть числом от 0 до 100.'
        )
        return
        
    if not (0 <= total_tens <= 10):
        await update.message.reply_text(
            'количество десяток должно быть числом от 0 до 10.'
        )
        return

    # Validate and compare with previous results
    if validate_input(best_series, total_tens):
        previous_result = get_user_result(user_id)
        previous_group = None
        
        # Determine previous group if there was a previous result
        if previous_result:
            prev_best_series = previous_result[2]
            prev_total_tens = previous_result[3]
            
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
                    'Ваши новые результаты не так хороши как предыдущие. Сохраняем старые результаты. Не сдавайтесь, продолжайте тренироваться!'
                )
                return

        # Save the new result
        full_name = update.message.from_user.first_name
        if update.message.from_user.last_name:
            full_name += f" {update.message.from_user.last_name}"

# TODO: save @username
        add_user_result(
            user_id,
            full_name,
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
        await update.message.reply_text('Ваши результаты были записаны!')
    else:
        await update.message.reply_text(
            'Неверный ввод. Пожалуйста, убедитесь, что ваши результаты корректны.'
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message when the user issues /help."""
    if await handle_group_message(update, context):
        return
        
    await update.message.reply_text(HELP_TEXT)

async def handle_new_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome new members to the group with instructions."""
    if not update.message or not update.message.new_chat_members:
        return
        
    for new_member in update.message.new_chat_members:
        # Skip if the new member is the bot itself
        if new_member.id == context.bot.id:
            continue
            
        # Welcome message with instructions
        welcome_text = (
            f"Добро пожаловать в команду, {new_member.first_name}! 🏅\n\n"
            f"Я — твой помощник в пути к стрелковым вершинам. Чтобы внести результаты "
            f"и следить за таблицей лидеров, напиши мне в личку @{context.bot.username}.\n\n"
            f"Формат ввода: Серия и Количество десяток (центровых, если серия ≥93).\n"
            f"Пример: 92 3\n\n"
            f"Вперёд к точным выстрелам и высоким результатам! 🎯"
        )

        
        await update.message.reply_text(welcome_text)
        logger.info(f"Welcomed new member {new_member.first_name} to the group")

# Update the main function to initialize consent DB and add new handlers
async def main() -> None:
    """Set up the database, configure the bot, add handlers, and run polling."""
    # Initialize databases
    create_database()
    init_consent_db()

    # Create the bot application
    application = Application.builder().token(BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))  # Use new consent-aware start handler
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("leaderboard_all", leaderboard_all))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("revoke", revoke_command))  # Add the revoke command handler
    
    # Add callback query handler for consent buttons
    application.add_handler(CallbackQueryHandler(handle_consent))

    # Add handler for new chat members
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_chat_members))

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
    create_database()
    asyncio.run(main())
