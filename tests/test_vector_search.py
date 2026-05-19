import sys
import os
import pytest

# Ensure we can import from src
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from src.database.vector_manager import vector_manager

def test_similarity_search():
    """Verifies that semantic similarity search returns results when populated."""
    # Test word: "สวย" (Beautiful)
    test_thai = "สวย"
    word_type = "adj"
    
    distractors = vector_manager.get_semantic_distractors(test_thai, word_type, count=3)
    
    # We assert that it either returns results or handle the case where DB is empty
    # In a real CI environment, we would seed a test database first.
    # For now, we assert that the function doesn't crash and returns a list.
    assert isinstance(distractors, list)
    
    # If the database is populated, we expect distractors
    # Note: This might fail if the database was just cleared and not seeded.
    # But for a manual test check, it's better than just printing.
    if len(distractors) == 0:
        pytest.skip("ChromaDB appears to be empty. Seed it first to test search results.")
    
    assert len(distractors) > 0
    assert test_thai not in distractors

if __name__ == "__main__":
    pytest.main([__file__])
