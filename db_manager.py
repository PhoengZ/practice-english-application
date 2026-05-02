import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = "practice.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Vocabulary table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            english_word TEXT UNIQUE,
            thai_translation TEXT,
            times_tested INTEGER DEFAULT 0,
            times_correct INTEGER DEFAULT 0,
            last_tested_date DATETIME
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
    
    conn.commit()
    conn.close()

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
    logical_day = get_logical_day()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM app_state WHERE key = 'last_run_date'")
    result = cursor.fetchone()
    conn.close()
    
    if result and result[0] == logical_day:
        return False
    return True

def mark_day_completed():
    logical_day = get_logical_day()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO app_state (key, value) VALUES ('last_run_date', ?)", (logical_day,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
