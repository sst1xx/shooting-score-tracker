"""Module for managing user consent data."""

import os
import sqlite3
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Get data directory from environment variable or use default
DATA_DIR = os.environ.get('DATA_DIR', './data')
os.makedirs(DATA_DIR, exist_ok=True)

# Constants
CONSENT_DB = os.path.join(DATA_DIR, 'consent.db')

def init_consent_db():
    """Initialize the consent database tables."""
    conn = sqlite3.connect(CONSENT_DB)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_consent (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            consent_given INTEGER,
            is_child INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("Consent database initialized")

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

def is_child_user(user_id):
    """Check if a user is marked as a child in the consent database.
    
    Args:
        user_id: The user's ID
        
    Returns:
        bool: True if the user is marked as a child, False otherwise
    """
    try:
        conn = sqlite3.connect(CONSENT_DB)
        cursor = conn.cursor()
        cursor.execute('SELECT is_child FROM user_consent WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None and result[0] == 1
    except Exception as e:
        logger.error(f"Error checking if user is a child: {e}")
        return False
        
def get_all_child_user_ids():
    """Get a list of all user IDs marked as children in the consent database.
    
    Returns:
        list: List of user IDs marked as children
    """
    try:
        conn = sqlite3.connect(CONSENT_DB)
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM user_consent WHERE is_child = 1 AND consent_given = 1')
        results = cursor.fetchall()
        conn.close()
        return [result[0] for result in results]  # Extract user_ids from results
    except Exception as e:
        logger.error(f"Error retrieving child users: {e}")
        return []

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
