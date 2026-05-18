import sys
import os

# Ensure we can import from src
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from src.database.vector_manager import vector_manager

def test_similarity_search():
    print("Testing semantic similarity search...")
    
    # Test word: "สวย" (Beautiful)
    test_thai = "เธชเธงเธข"
    word_type = "adj"
    
    print(f"Querying distractors for: {test_thai} ({word_type})")
    distractors = vector_manager.get_semantic_distractors(test_thai, word_type, count=3)
    
    print(f"Top distractors: {distractors}")
    
    if len(distractors) > 0:
        print("SUCCESS: Semantic distractors retrieved.")
    else:
        print("FAILURE: No distractors found. Check if ChromaDB is populated correctly.")

if __name__ == "__main__":
    test_similarity_search()
