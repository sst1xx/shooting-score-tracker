"""
User package for the shooting score tracker.
Handles user consent and group membership verification.
"""

# Import all functions from the consent module
from .consent import (
    init_consent_db,
    save_user_consent,
    check_user_consent,
    revoke_user_consent,
    CONSENT_DB
)

# Import all functions from the membership module
from .membership import (
    is_user_in_chat,
    is_user_in_group,
    _handle_telegram_error,
    _extract_new_group_id
)

# Import the group message handling function
from .messages import handle_group_message

# Import the leaderboard functions
from .leaderboard import leaderboard, leaderboard_all

# Import and expose admin functionality
from .admin import (
    is_admin,
    handle_admin_command,
    handle_admin_callback,
    modify_user_result,
    delete_user,
    register_admin_handlers
)

# Export all functions to maintain the same API
__all__ = [
    'init_consent_db',
    'save_user_consent',
    'check_user_consent',
    'revoke_user_consent',
    'CONSENT_DB',
    'is_user_in_chat',
    'is_user_in_group',
    '_handle_telegram_error',
    '_extract_new_group_id',
    'handle_group_message',
    'leaderboard',
    'leaderboard_all',
    'is_admin',
    'handle_admin_command',
    'handle_admin_callback',
    'modify_user_result',
    'delete_user',
    'register_admin_handlers'
]
