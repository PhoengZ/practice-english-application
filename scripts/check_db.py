import sqlite3
import os

DB_PATH = os.path.join("data", "practice.db")

def check_missing_translations():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM words WHERE thai_translation IS NULL OR thai_translation = ''")
    count = cursor.fetchone()[0]
    
    print(f"Total rows with missing translations: {count}")
    
    if count > 0:
        cursor.execute("SELECT english_word, word_type FROM words WHERE thai_translation IS NULL OR thai_translation = '' LIMIT 10")
        samples = cursor.fetchall()
        print("Samples:")
        for word, w_type in samples:
            print(f"- {word} ({w_type})")
            
    conn.close()

if __name__ == "__main__":
    check_missing_translations()
