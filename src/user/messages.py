import logging
from telegram import Update
from telegram.ext import ContextTypes

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
                    
                    # Use first name and last name if available, otherwise username
                    user = update.message.from_user
                    if user.first_name:
                        if user.last_name:
                            user_greeting = f"{user.first_name} {user.last_name}"
                        else:
                            user_greeting = user.first_name
                    else:
                        user_greeting = f"@{user.username}" if user.username else "Пользователь"
                    
                    # Reply only when mentioned
                    # await update.message.reply_text(
                    #     f'{user_greeting}, спасибо большое за интерес! 😊 '
                    #     'Напишите, пожалуйста, в личку — так удобнее внести статистику и не засорять чат 🙏\n\n'
                    #     f'С теплом, @{bot_username}'
                    # )


            # Always return True for group messages to prevent further processing
            return True
    except Exception as e:
        logger.error(f"Error in handle_group_message: {e}")
    
    return False  # Not a group message, proceed with normal handling
