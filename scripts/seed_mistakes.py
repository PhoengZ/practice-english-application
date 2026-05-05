import sqlite3
import random
from datetime import datetime, timedelta
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "practice.db")

def seed_mistakes():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all words
    cursor.execute("SELECT id, word_type, word_level FROM words")
    words = cursor.fetchall()
    
    if not words:
        print("No words found in DB. Run ingest first.")
        return

    print(f"Seeding mistakes for {len(words)} words...")
    
    for word_id, w_type, w_level in words:
        # Randomly decide if this word has been tested
        if random.random() > 0.7: # 30% of words tested
            times_tested = random.randint(1, 20)
            
            # Bias accuracy based on word level (C1 harder than A1)
            base_accuracy = 0.8
            if w_level == 'C1': base_accuracy = 0.4
            elif w_level == 'B2': base_accuracy = 0.5
            elif w_level == 'B1': base_accuracy = 0.6
            elif w_level == 'A2': base_accuracy = 0.7
            
            # Further bias by word type (verbs and adverbs might be harder)
            if w_type in ['v', 'adv']: base_accuracy -= 0.1
            
            times_correct = int(times_tested * (base_accuracy + random.uniform(-0.2, 0.2)))
            times_correct = max(0, min(times_tested, times_correct))
            
            last_tested = datetime.now() - timedelta(days=random.randint(0, 30))
            
            cursor.execute('''
                UPDATE words 
                SET times_tested = ?, times_correct = ?, last_tested_date = ?
                WHERE id = ?
            ''', (times_tested, times_correct, last_tested, word_id))
            
            # Also seed activity_log
            date_str = last_tested.strftime("%Y-%m-%d")
            cursor.execute('''
                INSERT INTO activity_log (date, words_practiced, correct_answers)
                VALUES (?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    words_practiced = words_practiced + excluded.words_practiced,
                    correct_answers = correct_answers + excluded.correct_answers
            ''', (date_str, times_tested, times_correct))

    conn.commit()
    conn.close()
    print("Seeding complete.")

if __name__ == "__main__":
    seed_mistakes()
