"""Module for managing shooting results data."""

import os
import sqlite3
import logging
from datetime import datetime
from config import DATA_DIR, DB_PATH  # Changed from: from ..config import DATA_DIR, DB_PATH

# Configure logging
logger = logging.getLogger(__name__)

def create_connection():
    """Create a database connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    return conn

def create_tables():
    """Create the necessary tables if they don't exist."""
    conn = create_connection()
    cursor = conn.cursor()
    
    # Create bot_data table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bot_data (
        id INTEGER PRIMARY KEY,
        key TEXT,
        value TEXT
    )
    ''')
    
    # Create user_results table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_results (
        user_id INTEGER PRIMARY KEY,
        full_name TEXT,
        best_series INTEGER,
        total_tens INTEGER,
        photo_id TEXT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

def create_database():
    """Create the database and necessary tables."""
    create_tables()
    logger.info("Results database initialized")

def add_user_result(user_id, full_name, best_series, total_tens, photo_id=None):
    """Add or update a user's shooting results."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_results (user_id, full_name, best_series, total_tens, photo_id)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            full_name = excluded.full_name,
            best_series = excluded.best_series,
            total_tens = excluded.total_tens,
            photo_id = excluded.photo_id
        WHERE excluded.best_series > user_results.best_series
           OR (excluded.best_series = user_results.best_series AND excluded.total_tens > user_results.total_tens)
    ''', (user_id, full_name, best_series, total_tens, photo_id))
    conn.commit()
    conn.close()

def get_user_result(user_id):
    """Get a user's shooting result."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, full_name, best_series, total_tens, photo_id FROM user_results 
        WHERE user_id = ?
    ''', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def validate_input(best_series, total_tens):
    """Validate that the input values are in acceptable ranges."""
    return (
        isinstance(best_series, int) and best_series >= 0
        and isinstance(total_tens, int) and total_tens >= 0
    )

def get_all_results():
    """Get all user results, ordered by best series and total tens."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, full_name, best_series, total_tens FROM user_results 
        ORDER BY best_series DESC, total_tens DESC
    ''')
    results = cursor.fetchall()
    conn.close()
    return results
