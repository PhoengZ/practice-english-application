import sqlite3
import os
from datetime import datetime, timedelta
from contextlib import contextmanager

# Ensure DB_PATH is absolute so it works from any directory
# Moved to root data folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "practice.db")

@contextmanager
def get_db_connection():
    """Context manager for SQLite database connection."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initializes the database schema."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Vocabulary table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                english_word TEXT,
                word_type TEXT,
                word_level TEXT,
                thai_translation TEXT,
                times_tested INTEGER DEFAULT 0,
                times_correct INTEGER DEFAULT 0,
                last_tested_date DATETIME,
                UNIQUE(english_word, word_type)
            )
        ''')
        
        # Activity log for dashboard
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_log (
                date DATE PRIMARY KEY,
                words_practiced INTEGER DEFAULT 0,
                correct_answers INTEGER DEFAULT 0
            )
        ''')
        
        # App state (rollover check)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        # Infinite mode scores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS infinite_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                score INTEGER,
                duration_seconds INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()

def save_infinite_score(score, duration_seconds):
    """Saves a score from an infinite mode session."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO infinite_scores (score, duration_seconds)
            VALUES (?, ?)
        ''', (score, duration_seconds))
        conn.commit()

def get_best_infinite_score():
    """Returns the highest score achieved in infinite mode."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(score) FROM infinite_scores")
        result = cursor.fetchone()
        return result[0] if result[0] is not None else 0

def get_infinite_history():
    """Returns all infinite mode scores."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT score, duration_seconds, timestamp FROM infinite_scores ORDER BY timestamp DESC")
        return cursor.fetchall()

def get_logical_day():
    """Returns the current date string adjusted for 7 AM rollover."""
    now = datetime.now()
    # If before 7 AM, it belongs to the previous calendar day
    if now.hour < 7:
        logical_day = now - timedelta(days=1)
    else:
        logical_day = now
    return logical_day.strftime("%Y-%m-%d")

def should_run_today():
    """Checks if the application should run today based on the logical day."""
    logical_day = get_logical_day()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM app_state WHERE key = 'last_run_date'")
        result = cursor.fetchone()
    
    if result and result[0] == logical_day:
        return False
    return True

def mark_day_completed():
    """Marks the current logical day as completed in the database."""
    logical_day = get_logical_day()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO app_state (key, value) VALUES ('last_run_date', ?)", (logical_day,))
        conn.commit()

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at: {DB_PATH}")
