import os
import logging
from typing import List, Tuple, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from database import add_user_result, get_user_result, create_database
from config import DB_PATH
import sqlite3

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load admin IDs from environment
def get_admin_ids() -> List[int]:
    """Get the list of admin user IDs from environment variables."""
    admin_ids_str = os.environ.get('ADMIN_IDS', '')
    if not admin_ids_str:
        return []
    
    try:
        # Parse comma-separated list of integers
        admin_ids = [int(id_str.strip()) for id_str in admin_ids_str.split(',') if id_str.strip()]
        return admin_ids
    except ValueError:
        logger.error("Invalid ADMIN_IDS format in environment variables")
        return []

def is_admin(user_id: int) -> bool:
    """Check if a user has admin privileges."""
    admin_ids = get_admin_ids()
    return user_id in admin_ids

# Helper function to check if a message is from a private chat
async def is_private_chat(update: Update) -> bool:
    """Check if the message was sent in a private chat."""
    return update.effective_chat.type == 'private'

async def handle_admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /admin command to access admin functions."""
    # Silently ignore if not in private chat
    if not await is_private_chat(update):
        return
    
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("У вас нет прав администратора.")
        return
    
    keyboard = [
        [InlineKeyboardButton("🔄 Изменить результат пользователя", callback_data='admin_modify')],
        [InlineKeyboardButton("🗑️ Удалить пользователя", callback_data='admin_delete')],
        [InlineKeyboardButton("📋 Список всех пользователей", callback_data='admin_list_users')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Панель администратора. Выберите действие:",
        reply_markup=reply_markup
    )

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin panel callback queries."""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Silently ignore if not in private chat
    if query.message.chat.type != 'private':
        await query.answer()  # Need to answer the callback but don't show any message
        return
    
    if not is_admin(user_id):
        await query.answer("У вас нет прав администратора.")
        return
    
    await query.answer()
    
    if query.data == 'admin_modify':
        await query.edit_message_text(
            "Отправьте команду в формате:\n"
            "/modify_user <user_id> <best_series> <total_tens>\n\n"
            "Например: /modify_user 123456789 95 6"
        )
    
    elif query.data == 'admin_delete':
        await query.edit_message_text(
            "Отправьте команду в формате:\n"
            "/delete_user <user_id>\n\n"
            "Например: /delete_user 123456789"
        )
    
    elif query.data == 'admin_list_users':
        # List all users in the database
        try:
            # Check if the database file exists
            if not os.path.exists(DB_PATH):
                await query.edit_message_text(
                    "❌ База данных не найдена."
                )
                return
            
            # Connect to database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Check if the table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_results'")
            if not cursor.fetchone():
                await query.edit_message_text(
                    "❌ Таблица 'user_results' не найдена в базе данных."
                )
                conn.close()
                return
            
            # Get all users
            cursor.execute("SELECT user_id, full_name, best_series, total_tens FROM user_results ORDER BY best_series DESC, total_tens DESC")
            users = cursor.fetchall()
            conn.close()
            
            if not users:
                await query.edit_message_text("📋 База данных пользователей пуста.")
                return
                
            # Format list of users
            users_text = "📋 Список всех пользователей:\n\n"
            for i, (uid, name, series, tens) in enumerate(users, 1):
                users_text += f"{i}. {name} (ID: {uid}) - Серия: {series}, Десятки: {tens}\n"
                
                # Telegram has a message length limit, split into multiple messages if needed
                if i % 40 == 0 and i < len(users):
                    await query.edit_message_text(users_text)
                    users_text = "📋 Список пользователей (продолжение):\n\n"
            
            await query.edit_message_text(users_text)
            
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            await query.edit_message_text(
                f"❌ Произошла ошибка при получении списка пользователей:\n{str(e)}"
            )

# Helper function to send responses that works with both message and callback query updates
async def send_response(update: Update, text: str) -> None:
    """Send a response that works with both message and callback query updates."""
    if update.callback_query:
        await update.callback_query.message.edit_text(text)
    elif update.message:
        await update.message.reply_text(text)
    else:
        logger.error("Unable to respond: update contains neither message nor callback_query")

async def modify_user_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Modify a user's shooting result (admin only)."""
    # Silently ignore if not in private chat
    if not await is_private_chat(update):
        return
    
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await send_response(update, "У вас нет прав администратора.")
        return
    
    # Check if we have enough arguments
    if not context.args or len(context.args) < 3:
        await send_response(update, 
            "Неверный формат команды. Используйте:\n"
            "/modify_user <user_id> <best_series> <total_tens>"
        )
        return
    
    try:
        target_user_id = int(context.args[0])
        best_series = int(context.args[1])
        total_tens = int(context.args[2])
        
        # Validate ranges
        if not (0 <= best_series <= 100):
            await send_response(update, "Результат серии должен быть от 0 до 100.")
            return
            
        if not (0 <= total_tens <= 10):
            await send_response(update, "Количество десяток должно быть от 0 до 10.")
            return
        
        # Check if user exists
        user_data = get_user_result(target_user_id)
        
        if not user_data:
            await send_response(update, f"Пользователь с ID {target_user_id} не найден в базе данных.")
            return
        
        # Update the user's result
        full_name = user_data[1]  # Get username from existing record
        add_user_result(target_user_id, full_name, best_series, total_tens)
        
        await send_response(update,
            f"Результат пользователя {full_name} (ID: {target_user_id}) обновлен:\n"
            f"Серия: {best_series}, Десятки: {total_tens}"
        )
        
        logger.info(f"Admin {update.effective_user.id} modified result for user {target_user_id}")
        
    except ValueError:
        await send_response(update, "Ошибка в формате данных. Убедитесь, что ID пользователя и результаты - числа.")
    except Exception as e:
        logger.error(f"Error modifying user result: {e}")
        await send_response(update, f"Произошла ошибка: {str(e)}")

async def delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete a user from the scoreboard database (admin only)."""
    # Silently ignore if not in private chat
    if not await is_private_chat(update):
        return
    
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await send_response(update, "У вас нет прав администратора.")
        return
    
    # Check if we have the user_id argument
    if not context.args or len(context.args) < 1:
        await send_response(update,
            "Неверный формат команды. Используйте:\n"
            "/delete_user <user_id>"
        )
        return
    
    try:
        target_user_id = int(context.args[0])
        
        # Check if user exists and get their name before deletion
        user_data = get_user_result(target_user_id)
        
        if not user_data:
            await send_response(update, f"Пользователь с ID {target_user_id} не найден в базе данных.")
            return
        
        full_name = user_data[1]
        
        # Connect to the database using the centralized path
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM user_results WHERE user_id = ?", (target_user_id,))
        conn.commit()
        conn.close()
        
        await send_response(update,
            f"Пользователь {full_name} (ID: {target_user_id}) удален из базы данных."
        )
        
        logger.info(f"Admin {update.effective_user.id} deleted user {target_user_id} from database")
        
    except ValueError:
        await send_response(update, "Ошибка в формате данных. Убедитесь, что ID пользователя - число.")
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        await send_response(update, f"Произошла ошибка: {str(e)}")

# Function to register admin handlers to the application
def register_admin_handlers(application):
    """Register all admin-related handlers to the application."""
    application.add_handler(CommandHandler("admin", handle_admin_command))
    application.add_handler(CallbackQueryHandler(handle_admin_callback, pattern=r'^admin_'))
    application.add_handler(CommandHandler("modify_user", modify_user_result))
    application.add_handler(CommandHandler("delete_user", delete_user))