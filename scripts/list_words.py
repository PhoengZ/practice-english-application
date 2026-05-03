import sqlite3
import sys
import io
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys
sys.path.append(BASE_DIR)
from src.database.db_manager import DB_PATH

# Fix Windows encoding for Thai characters
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def list_all_words():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT english_word, word_type, word_level, thai_translation, times_tested, times_correct FROM words")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("No words found in the database.")
        return

    print(f"Total Words in Database: {len(rows)}")
    print(f"{'English':<20} | {'Type':<10} | {'Level':<6} | {'Thai':<20} | {'Tested':<8} | {'Correct':<8}")
    print("-" * 90)
    for eng, w_type, level, thai, tested, correct in rows:
        print(f"{eng:<20} | {w_type:<10} | {level:<6} | {thai:<20} | {tested:<8} | {correct:<8}")

if __name__ == "__main__":
    list_all_words()
