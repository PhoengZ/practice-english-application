import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.database.db_manager import get_db_connection
from src.core.typhoon_utils import translate_to_thai_batch

def fix_translations():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Fetch rows with missing translations
        cursor.execute("SELECT id, english_word, word_type FROM words WHERE thai_translation IS NULL OR thai_translation = ''")
        rows = cursor.fetchall()
        
        if not rows:
            print("No missing translations found.")
            return

        print(f"Found {len(rows)} rows to fix.")
        
        # 2. Prepare for batch translation
        word_type_pairs = [(row[1], row[2]) for row in rows]
        id_map = {f"{row[1]}|{row[2]}": row[0] for row in rows}
        
        # 3. Translate
        print("Requesting translations from Typhoon API...")
        translations = translate_to_thai_batch(word_type_pairs)
        
        # 4. Update database
        updated_count = 0
        for key, thai in translations.items():
            if key in id_map:
                word_id = id_map[key]
                cursor.execute("UPDATE words SET thai_translation = ? WHERE id = ?", (thai, word_id))
                updated_count += 1
        
        conn.commit()
        print(f"Successfully updated {updated_count} translations.")

if __name__ == "__main__":
    fix_translations()
