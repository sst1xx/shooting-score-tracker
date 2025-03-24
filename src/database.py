import os
import sqlite3

# Create data directory if it doesn't exist
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# Unified database path
DB_PATH = os.path.join(DATA_DIR, 'scoreboard.db')

def create_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn

def create_tables():
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
        username TEXT,
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

def add_user_result(user_id, username, best_series, total_tens, photo_id=None):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_results (user_id, username, best_series, total_tens, photo_id)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            best_series = excluded.best_series,
            total_tens = excluded.total_tens,
            photo_id = excluded.photo_id
        WHERE excluded.best_series > user_results.best_series
           OR (excluded.best_series = user_results.best_series AND excluded.total_tens > user_results.total_tens)
    ''', (user_id, username, best_series, total_tens, photo_id))
    conn.commit()
    conn.close()

def get_leaderboard():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT username, best_series, total_tens 
        FROM user_results
        ORDER BY best_series DESC, total_tens DESC
        LIMIT 10
    ''')
    leaderboard = cursor.fetchall()
    conn.close()
    return leaderboard

def reset_database():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM user_results')
    conn.commit()
    conn.close()

def get_user_result(user_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_results WHERE user_id = ?', (user_id,))
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
    """
    Retrieve all stored user results from the database.
    
    Returns:
        List of tuples containing (user_id, username, best_series, total_tens, photo_id)
    """
    conn = create_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM user_results')
    results = cursor.fetchall()
    
    conn.close()
    return results
