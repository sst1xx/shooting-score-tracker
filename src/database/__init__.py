"""Database package for the shooting score tracker."""

from .consent_db import (
    init_consent_db,
    save_user_consent,
    check_user_consent,
    revoke_user_consent
)

from .results_db import (
    create_database,
    add_user_result,
    get_user_result,
    validate_input,
    get_all_results,
    format_display_name  # Import from results_db.py instead of defining here
)

# Export all functions
__all__ = [
    'init_consent_db',
    'save_user_consent',
    'check_user_consent',
    'revoke_user_consent',
    'create_database',
    'add_user_result',
    'get_user_result',
    'validate_input',
    'get_all_results',
    'format_display_name'
]
