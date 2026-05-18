import sys
import os

# Ensure we can import from src
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from src.ui.app import get_distractors
from src.database.db_manager import get_db_connection

def test_pos_matching():
    print("Testing PoS matching for distractors...")
    
    # Test with a verb
    word_type = 'v'
    correct_thai = 'เธขเธญเธกเธฃเธฑเธ' # accept (v)
    
    distractors = get_distractors(correct_thai, word_type=word_type, count=3)
    print(f"Distractors for type '{word_type}': {distractors}")
    
    # Verify in DB if they are actually verbs
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for d in distractors:
            if d.startswith("Incorrect Option"):
                continue
            cursor.execute("SELECT word_type FROM words WHERE thai_translation = ?", (d,))
            types = [row[0] for row in cursor.fetchall()]
            print(f"Word '{d}' has types: {types}")
            if word_type not in types:
                print(f"FAILURE: Word '{d}' is not of type '{word_type}'")
            else:
                print(f"SUCCESS: Word '{d}' matches type '{word_type}'")

    # Test with a noun
    word_type = 'n'
    correct_thai = 'เธเธฑเธเธต' # account (n)
    distractors = get_distractors(correct_thai, word_type=word_type, count=3)
    print(f"\nDistractors for type '{word_type}': {distractors}")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for d in distractors:
            if d.startswith("Incorrect Option"):
                continue
            cursor.execute("SELECT word_type FROM words WHERE thai_translation = ?", (d,))
            types = [row[0] for row in cursor.fetchall()]
            print(f"Word '{d}' has types: {types}")
            if word_type not in types:
                print(f"FAILURE: Word '{d}' is not of type '{word_type}'")
            else:
                print(f"SUCCESS: Word '{d}' matches type '{word_type}'")

if __name__ == "__main__":
    test_pos_matching()
