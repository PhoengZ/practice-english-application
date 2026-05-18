import sqlite3
import random
import sys
import subprocess
import os
from datetime import datetime

# Ensure we can import from src when running from any directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from src.database.db_manager import (
    should_run_today, mark_day_completed, DB_PATH, get_logical_day, 
    get_db_connection, save_infinite_score, get_best_infinite_score
)

from src.database.vector_manager import vector_manager

def get_words_for_practice(count=10):
    """Fetches words for practice."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if count:
            # Prioritize words least tested or least correct for daily practice
            cursor.execute('''
                SELECT id, english_word, word_type, word_level, thai_translation 
                FROM words 
                ORDER BY times_tested ASC, times_correct ASC, RANDOM() 
                LIMIT ?
            ''', (count,))
        else:
            # Random order for infinite mode
            cursor.execute('''
                SELECT id, english_word, word_type, word_level, thai_translation 
                FROM words 
                ORDER BY RANDOM()
            ''')
        return cursor.fetchall()

def get_distractors(correct_thai, word_type=None, count=3):
    """Fetches semantic distractors from VectorDB, falling back to random SQL if needed."""
    distractors = []
    
    # 1. Try semantic search from VectorDB
    try:
        distractors = vector_manager.get_semantic_distractors(correct_thai, word_type, count)
    except Exception as e:
        print(f"Warning: Semantic search failed, falling back to random: {e}")

    # 2. If not enough semantic distractors, fill with random words of same type from SQL
    if len(distractors) < count:
        remaining = count - len(distractors)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Construct exclusion clause
            exclude_list = [correct_thai] + distractors
            placeholders = ', '.join(['?'] * len(exclude_list))
            
            query = f'''
                SELECT thai_translation 
                FROM words 
                WHERE thai_translation NOT IN ({placeholders})
                AND word_type = ?
                GROUP BY thai_translation
                ORDER BY RANDOM() 
                LIMIT ?
            '''
            cursor.execute(query, tuple(exclude_list + [word_type, remaining]))
            sql_distractors = [row[0] for row in cursor.fetchall()]
            distractors.extend(sql_distractors)

    # 3. Last resort: Fill with any random words if still not enough
    if len(distractors) < count:
        remaining = count - len(distractors)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            exclude_list = [correct_thai] + distractors
            placeholders = ', '.join(['?'] * len(exclude_list))
            
            query = f'''
                SELECT thai_translation 
                FROM words 
                WHERE thai_translation NOT IN ({placeholders})
                GROUP BY thai_translation
                ORDER BY RANDOM() 
                LIMIT ?
            '''
            cursor.execute(query, tuple(exclude_list + [remaining]))
            distractors.extend([row[0] for row in cursor.fetchall()])
    
    while len(distractors) < count:
        distractors.append(f"Incorrect Option {len(distractors)+1}")
        
    random.shuffle(distractors)
    return distractors

def update_word_stats(word_id, is_correct):
    """Updates the statistics for a specific word."""
    with get_db_connection() as conn:
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
        
        logical_day = get_logical_day()
        cursor.execute('''
            INSERT INTO activity_log (date, words_practiced, correct_answers)
            VALUES (?, 1, ?)
            ON CONFLICT(date) DO UPDATE SET
                words_practiced = words_practiced + 1,
                correct_answers = correct_answers + ?
        ''', (logical_day, 1 if is_correct else 0, 1 if is_correct else 0))
        conn.commit()

def run_infinite_mode():
    """Runs the infinite mode: continues until the first mistake."""
    print("\n" + "="*40)
    print("🚀 INFINITE MODE: SUDDEN DEATH")
    print("Answer correctly to keep going.")
    print("One mistake and the game ends!")
    print("="*40 + "\n")

    best_score = get_best_infinite_score()
    print(f"Current High Score: {best_score}")

    score = 0
    start_time = datetime.now()

    while True:
        words = get_words_for_practice(count=1)
        if not words:
            print("No vocabulary found!")
            break

        word_id, eng, w_type, level, thai = words[0]
        print(f"\nWord {score + 1}: {eng} ({w_type}) [{level}]")

        choices = get_distractors(thai, word_type=w_type) + [thai]
        random.shuffle(choices)

        for idx, choice in enumerate(choices):
            print(f"{idx + 1}. {choice}")

        user_input = input("\nYour choice (or 'exit'): ").strip()

        if user_input.lower() == 'exit':
            break

        try:
            choice_idx = int(user_input) - 1
            if 0 <= choice_idx < len(choices):
                selected = choices[choice_idx]
                if selected == thai:
                    print("✅ Correct!")
                    update_word_stats(word_id, True)
                    score += 1
                else:
                    print(f"❌ Wrong! The correct answer was: {thai}")
                    update_word_stats(word_id, False)
                    break
            else:
                print(f"Please enter a number between 1 and {len(choices)}.")
        except ValueError:
            print("Invalid input. Enter a number or 'exit'.")

    end_time = datetime.now()
    duration = int((end_time - start_time).total_seconds())
    save_infinite_score(score, duration)

    print(f"\nGame Over! Final Score: {score}")
    if score > best_score:
        print(f"🏆 NEW HIGH SCORE! (Previous: {best_score})")
    else:
        print(f"High Score: {best_score}")
    print(f"Time played: {duration // 60}m {duration % 60}s")

def run_daily_practice():
    """Orchestrates the daily practice session."""
    print("\n=== Daily Practice Session ===")
    words = get_words_for_practice(count=10)
    if not words:
        print("No vocabulary found!")
        return

    score = 0
    total = len(words)

    for i, (word_id, eng, w_type, level, thai) in enumerate(words):
        print(f"\nWord {i+1}/{total}: {eng} ({w_type}) [{level}]")
        choices = get_distractors(thai, word_type=w_type) + [thai]
        random.shuffle(choices)
        
        for idx, choice in enumerate(choices):
            print(f"{idx + 1}. {choice}")
        
        while True:
            user_input = input("\nYour choice (or 'exit'): ").strip()
            if user_input.lower() == 'exit':
                sys.exit(0)

            try:
                choice_idx = int(user_input) - 1
                if 0 <= choice_idx < len(choices):
                    if choices[choice_idx] == thai:
                        print("✅ Correct!")
                        update_word_stats(word_id, True)
                        score += 1
                    else:
                        print(f"❌ Wrong. Correct: {thai}")
                        update_word_stats(word_id, False)
                    break
                else:
                    print(f"Please enter 1-{len(choices)}.")
            except ValueError:
                print("Invalid input.")

    print(f"\nSession Finished! Score: {score}/{total}")
    mark_day_completed()

def show_dashboard():
    print("Opening Dashboard...")
    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.py")
    subprocess.Popen([sys.executable, "-m", "streamlit", "run", dashboard_path])

if __name__ == "__main__":
    wants_dashboard = len(sys.argv) > 1 and sys.argv[1].lower() == 'dashboard'
    is_startup = len(sys.argv) > 1 and sys.argv[1].lower() == '--startup'
    force_run = len(sys.argv) > 1 and sys.argv[1].lower() == '--force'

    if is_startup:
        if should_run_today():
            run_daily_practice()
        sys.exit(0)
    
    if wants_dashboard:
        show_dashboard()
        sys.exit(0)
        
    if force_run:
        run_daily_practice()
        sys.exit(0)

    while True:
        print("\n--- Welcome to Practice English ---")
        print("1. Daily Practice")
        print("2. Infinite Mode (Sudden Death)")
        print("3. Dashboard")
        print("4. Exit")
        
        choice = input("\nSelect an option: ").strip()
        
        if choice == '1':
            run_daily_practice()
            break
        elif choice == '2':
            run_infinite_mode()
            break
        elif choice == '3':
            show_dashboard()
        elif choice == '4':
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")
