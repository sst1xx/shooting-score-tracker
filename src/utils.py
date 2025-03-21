from telegram import Bot
from telegram.error import TelegramError, BadRequest, Forbidden, TimedOut
import logging
import re
from typing import Tuple, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Store the current group ID in memory (initialized from config)
_current_group_id = None

async def is_user_in_chat(bot: Bot, user_id: int, chat_id: int) -> bool:
    """
    Проверяет, находится ли пользователь в указанном чате (группе или супергруппе).
    
    :param bot: Объект бота
    :param user_id: ID пользователя для проверки
    :param chat_id: ID чата
    :return: True, если пользователь в чате, иначе False
    """
    try:
        # 1. Проверить, что чат является группой или супергруппой
        chat = await bot.get_chat(chat_id)
        if chat.type not in ["group", "supergroup"]:
            logger.warning(f"Чат {chat_id} не является группой: {chat.type}")
            return False

        # 2. Проверить наличие пользователя в чате
        member = await bot.get_chat_member(chat_id, user_id)
        is_member = member.status in ["member", "administrator", "creator"]
        
        logger.info(f"Пользователь {user_id} {'является' if is_member else 'НЕ является'} членом группы {chat_id}")
        return is_member

    except TelegramError as e:
        logger.error(f"Ошибка Telegram при проверке членства в чате: {e}")
        return False

async def is_user_in_group(user_id: int, bot: Bot) -> Tuple[bool, str]:
    """
    Проверяет, является ли пользователь участником группы, указанной в GROUP_ID.
    
    Args:
        user_id: ID пользователя для проверки
        bot: Объект бота
        
    Returns:
        Tuple (is_member, error_message)
    """
    global _current_group_id
    
    # Initialize _current_group_id from config if not set yet
    if _current_group_id is None:
        from config import GROUP_ID
        _current_group_id = GROUP_ID
        logger.info(f"Инициализирован ID группы: {_current_group_id}")
    
    try:
        # Convert _current_group_id to int if it's a string
        group_id = int(_current_group_id)
        
        logger.info(f"Проверка членства пользователя {user_id} в группе {group_id}")
        
        # Check membership
        is_member = await is_user_in_chat(bot=bot, user_id=user_id, chat_id=group_id)
        
        if is_member:
            return True, ""
        else:
            return False, "Вы не являетесь участником группы. Пожалуйста, присоединитесь к группе для использования бота."
            
    except TelegramError as e:
        return await _handle_telegram_error(e, bot, user_id)
    except Exception as e:
        logger.error(f"Ошибка при проверке членства в группе: {e}")
        return False, "Произошла ошибка при проверке членства в группе."

async def _handle_telegram_error(e: TelegramError, bot: Bot, user_id: int) -> Tuple[bool, str]:
    """
    Обрабатывает ошибки Telegram API при проверке членства в группе.
    
    Args:
        e: Объект ошибки TelegramError
        bot: Объект бота
        user_id: ID пользователя
        
    Returns:
        Tuple (is_member, error_message)
    """
    global _current_group_id
    error_msg = str(e)
    
    # Handle group migration (but don't update _current_group_id)
    if "Group migrated to supergroup" in error_msg:
        logger.info(f"Group migrated to supergroup: {error_msg}")
        new_group_id = _extract_new_group_id(error_msg)
        if new_group_id:
            logger.info(f"Detected new group ID: {new_group_id}")
            logger.warning("Group ID has changed but will not be automatically updated")
            
            # Simply notify about migration but don't update _current_group_id
            return False, ("Группа была мигрирована в супергруппу. "
                           "Пожалуйста, обратитесь к администратору для обновления настроек бота.")
        
        return False, "Не удалось определить новый ID группы после миграции."
    
    # Handle specific errors
    logger.error(f"Telegram error при проверке членства: {error_msg}")
    
    if isinstance(e, BadRequest):
        error_lower = error_msg.lower()
        if "user not found" in error_lower:
            return False, "Вы не найдены в группе. Пожалуйста, вступите в группу."
        if "chat not found" in error_lower:
            logger.warning(f"Chat not found: {_current_group_id}")
            return False, "Группа не найдена. Пожалуйста, свяжитесь с администратором."
    
    if isinstance(e, Forbidden):
        logger.critical(f"Bot does not have access to the group: {error_msg}")
        return False, "Бот не имеет доступа к группе. Пожалуйста, свяжитесь с администратором."
    
    if isinstance(e, TimedOut):
        logger.warning("Timeout when querying Telegram API")
        return False, "Превышено время ожидания ответа от Telegram. Попробуйте позже."
    
    # For any other errors
    logger.warning(f"Unexpected error checking group membership: {error_msg}")
    return False, "Произошла неожиданная ошибка при проверке членства в группе."

def _extract_new_group_id(error_msg: str) -> Optional[str]:
    """
    Extract the new group ID from migration error message.
    
    Args:
        error_msg: Error message from Telegram
        
    Returns:
        New group ID or None if not found
    """
    match = re.search(r'new chat id: (-\d+)', error_msg.lower())
    if match:
        return match.group(1)
    return None