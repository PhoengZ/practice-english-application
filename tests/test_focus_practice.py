import sys
import os
import io

# Fix Windows encoding for Thai characters
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Ensure we can import from src
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from src.ui.app import get_words_for_practice_with_focus

def test_level_focus_query():
    """Verifies that filtering words by CEFR level works correctly."""
    for level in ['A1', 'A2', 'B1', 'B2']:
        words = get_words_for_practice_with_focus(focus_type='level', focus_value=level, count=5)
        assert len(words) > 0, f"No words returned for level {level}"
        for w in words:
            # Word structure: (id, english_word, word_type, word_level, thai_translation)
            assert w[3] == level, f"Word {w[1]} has level {w[3]}, expected {level}"
            
def test_verb_focus_query():
    """Verifies that verb filtering maps to verb sub-types ('v', 'auxiliary v', 'modal v')."""
    words = get_words_for_practice_with_focus(focus_type='type', focus_value='v', count=5)
    assert len(words) > 0, "No verbs returned"
    valid_verb_types = {'v', 'auxiliary v', 'modal v'}
    for w in words:
        assert w[2] in valid_verb_types, f"Word {w[1]} has type {w[2]}, expected one of {valid_verb_types}"

def test_noun_focus_query():
    """Verifies that noun filtering maps to noun sub-types ('n', 'noun')."""
    words = get_words_for_practice_with_focus(focus_type='type', focus_value='n', count=5)
    assert len(words) > 0, "No nouns returned"
    valid_noun_types = {'n', 'noun'}
    for w in words:
        assert w[2] in valid_noun_types, f"Word {w[1]} has type {w[2]}, expected one of {valid_noun_types}"

def test_adj_adv_focus_query():
    """Verifies that adjective and adverb filtering maps correctly."""
    # Test Adjectives
    adj_words = get_words_for_practice_with_focus(focus_type='type', focus_value='adj', count=5)
    assert len(adj_words) > 0, "No adjectives returned"
    for w in adj_words:
        assert w[2] == 'adj', f"Word {w[1]} has type {w[2]}, expected 'adj'"
        
    # Test Adverbs
    adv_words = get_words_for_practice_with_focus(focus_type='type', focus_value='adv', count=5)
    assert len(adv_words) > 0, "No adverbs returned"
    for w in adv_words:
        assert w[2] == 'adv', f"Word {w[1]} has type {w[2]}, expected 'adv'"

def test_other_focus_query():
    """Verifies that other type filtering excludes standard POS categories."""
    words = get_words_for_practice_with_focus(focus_type='type', focus_value='other', count=5)
    assert len(words) > 0, "No other type words returned"
    standard_types = {'v', 'auxiliary v', 'modal v', 'n', 'noun', 'adj', 'adv'}
    for w in words:
        assert w[2] not in standard_types, f"Word {w[1]} has standard type {w[2]}, which should be excluded"

if __name__ == "__main__":
    print("Running Focusing Mode Practice tests...")
    try:
        test_level_focus_query()
        print("[SUCCESS] test_level_focus_query passed!")
        
        test_verb_focus_query()
        print("[SUCCESS] test_verb_focus_query passed!")
        
        test_noun_focus_query()
        print("[SUCCESS] test_noun_focus_query passed!")
        
        test_adj_adv_focus_query()
        print("[SUCCESS] test_adj_adv_focus_query passed!")
        
        test_other_focus_query()
        print("[SUCCESS] test_other_focus_query passed!")
        
        print("\n[SUCCESS] ALL TESTS PASSED SUCCESSFULLY!")
    except AssertionError as e:
        print(f"[FAILURE] TEST FAILED: {e}")
        sys.exit(1)
