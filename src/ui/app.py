import sqlite3
import random
import sys
import subprocess
import os
import io
from datetime import datetime

# Ensure we can import from src when running from any directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from src.database.db_manager import should_run_today, mark_day_completed, DB_PATH, get_logical_day

def get_words_for_practice(count=10):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Prioritize words least tested or least correct
    cursor.execute('''
        SELECT id, english_word, word_type, word_level, thai_translation 
        FROM words 
        ORDER BY times_tested ASC, times_correct ASC, RANDOM() 
        LIMIT ?
    ''', (count,))
    words = cursor.fetchall()
    conn.close()
    return words

def get_distractors(correct_thai, count=3):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT thai_translation 
        FROM words 
        WHERE thai_translation != ? 
        GROUP BY thai_translation
        ORDER BY RANDOM() 
        LIMIT ?
    ''', (correct_thai, count))
    distractors = [row[0] for row in cursor.fetchall()]
    conn.close()
    # If not enough distractors in DB, add some placeholders
    while len(distractors) < count:
        distractors.append(f"Incorrect Option {len(distractors)+1}")
    return distractors

def update_word_stats(word_id, is_correct):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now()
    if is_correct:
        cursor.execute('''
            UPDATE words 
            SET times_tested = times_tested + 1, 
                times_correct = times_correct + 1, 
                last_tested_date = ? 
            WHERE id = ?
        ''', (now, word_id))
    else:
        cursor.execute('''
            UPDATE words 
            SET times_tested = times_tested + 1, 
                last_tested_date = ? 
            WHERE id = ?
        ''', (now, word_id))
    
    # Update activity log
    logical_day = get_logical_day()
    cursor.execute('''
        INSERT INTO activity_log (date, words_practiced, correct_answers)
        VALUES (?, 1, ?)
        ON CONFLICT(date) DO UPDATE SET
            words_practiced = words_practiced + 1,
            correct_answers = correct_answers + ?
    ''', (logical_day, 1 if is_correct else 0, 1 if is_correct else 0))
    
    conn.commit()
    conn.close()

def run_practice():
    print("=== English Practice Session ===")
    print("Commands: 'Rest' to stop today, 'Dashboard' to view progress")
    
    words = get_words_for_practice()
    if not words:
        print("No vocabulary found. Please ingest some words first!")
        return

    score = 0
    total = len(words)

    for i, (word_id, eng, w_type, level, thai) in enumerate(words):
        print(f"\nWord {i+1}/{total}: {eng} ({w_type}) [{level}]")
        
        choices = get_distractors(thai) + [thai]
        random.shuffle(choices)
        
        for idx, choice in enumerate(choices):
            print(f"{idx + 1}. {choice}")
        
        while True:
            user_input = input("\nYour choice (or command): ").strip()
            
            if user_input.lower() == 'rest':
                print("Resting for the day. See you tomorrow!")
                mark_day_completed()
                sys.exit(0)
            
            if user_input.lower() == 'dashboard':
                print("Opening Dashboard...")
                # Get the absolute path to dashboard.py
                dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.py")
                subprocess.Popen(["streamlit", "run", dashboard_path], shell=True)
                continue

            try:
                choice_idx = int(user_input) - 1
                if 0 <= choice_idx < len(choices):
                    selected = choices[choice_idx]
                    if selected == thai:
                        print("Correct! Excellent.")
                        update_word_stats(word_id, True)
                        score += 1
                    else:
                        print(f"Wrong. The correct answer was: {thai}")
                        update_word_stats(word_id, False)
                    break
                else:
                    print(f"Please enter a number between 1 and {len(choices)}.")
            except ValueError:
                print("Invalid input. Enter a number, 'Rest', or 'Dashboard'.")

    print(f"\nSession Finished! Score: {score}/{total}")
    mark_day_completed()

if __name__ == "__main__":
    # Check for command line arguments
    force_run = len(sys.argv) > 1 and sys.argv[1].lower() == '--force'
    wants_dashboard = len(sys.argv) > 1 and sys.argv[1].lower() == 'dashboard'

    if should_run_today() or force_run:
        run_practice()
    elif wants_dashboard:
        print("Opening Dashboard...")
        dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.py")
        subprocess.Popen(["streamlit", "run", dashboard_path], shell=True)
    else:
        print("Already practiced today! See you after 7 AM tomorrow.")
        print("💡 Tip: Use 'Practice' command to force start anyway.")
