import sqlite3
import os
import sys

# Ensure we can import from src
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from src.database.vector_manager import vector_manager

# Path to the backup database
BACKUP_DB_PATH = os.path.join(ROOT_DIR, "data", "backups", "practice_backup_init.db")

def migrate_data():
    if not os.path.exists(BACKUP_DB_PATH):
        print(f"Error: Backup database not found at {BACKUP_DB_PATH}")
        return

    print(f"Connecting to backup database: {BACKUP_DB_PATH}")
    conn = sqlite3.connect(BACKUP_DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, thai_translation, word_type, english_word FROM words")
        words = cursor.fetchall()
        total = len(words)
        print(f"Found {total} words to migrate.")

        batch_size = 100
        current_batch = []
        
        for i, (word_id, thai, w_type, eng) in enumerate(words):
            if not thai:
                continue
            
            current_batch.append((word_id, thai, w_type))
            
            if len(current_batch) >= batch_size:
                ids, thais, types = zip(*current_batch)
                vector_manager.add_batch_to_vector_db(list(ids), list(thais), list(types))
                current_batch = []
                print(f"Migrated {i + 1}/{total} words... (Current: {eng})")

        # Handle remaining words in the last batch
        if current_batch:
            ids, thais, types = zip(*current_batch)
            vector_manager.add_batch_to_vector_db(list(ids), list(thais), list(types))
            print(f"Migrated all {total} words.")

        print("\nMigration completed successfully!")
    except Exception as e:
        print(f"An error occurred during migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_data()
