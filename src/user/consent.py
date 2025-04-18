import os
import logging
import sqlite3
from typing import Optional
# Import init_consent_db from database.consent_db
from database.consent_db import init_consent_db

# Configure logging
logger = logging.getLogger(__name__)

# Constants
CONSENT_DB = os.path.join('data', 'consent.db')

# ==== CONSENT DATABASE FUNCTIONS ====
# init_consent_db function removed - now imported from database.consent_db

def save_user_consent(user_id, username, first_name):
    """Save user consent to the database."""
    try:
        conn = sqlite3.connect(CONSENT_DB)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO user_consent (user_id, username, first_name, consent_given)
            VALUES (?, ?, ?, 1)
        ''', (user_id, username, first_name))
        conn.commit()
        conn.close()
        logger.info(f"User {username} (ID: {user_id}) has given consent")
        return True
    except Exception as e:
        logger.error(f"Error saving user consent: {e}")
        return False

def check_user_consent(user_id):
    """Check if user has given consent."""
    try:
        conn = sqlite3.connect(CONSENT_DB)
        cursor = conn.cursor()
        cursor.execute('SELECT consent_given FROM user_consent WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None and result[0] == 1
    except Exception as e:
        logger.error(f"Error checking user consent: {e}")
        return False

def revoke_user_consent(user_id):
    """Revoke a user's consent."""
    try:
        conn = sqlite3.connect(CONSENT_DB)
        cursor = conn.cursor()
        cursor.execute('UPDATE user_consent SET consent_given = 0 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
        logger.info(f"User ID {user_id} has revoked consent")
        return True
    except Exception as e:
        logger.error(f"Error revoking user consent: {e}")
        return False
