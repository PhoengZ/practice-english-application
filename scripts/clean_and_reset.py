import os
import sqlite3
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Scripts are now in scripts/ folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "practice.db")
INPUT_FILE = os.path.join(BASE_DIR, "data", "oxford.txt")
CLEAN_FILE = os.path.join(BASE_DIR, "data", "oxford_clean.txt")
TYPHOON_API_KEY = os.getenv("TYPHOON_API_KEY")

# Add root to sys.path to allow imports from src
import sys
sys.path.append(BASE_DIR)
from src.core.ingest import ingest_from_text
from src.database.db_manager import init_db, get_db_connection
from src.database.vector_manager import vector_manager

client = OpenAI(api_key=TYPHOON_API_KEY, base_url="https://api.opentyphoon.ai/v1")

def clean_database():
    """Wipes the database tables and VectorDB to start fresh."""
    print("🧹 Cleaning database...")
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # Also clear VectorDB - do this first, if it fails, we haven't touched SQLite
        vector_manager.clear_all()

        # Wipe tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='words'")
        if cursor.fetchone():
            cursor.execute("DELETE FROM words")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='activity_log'")
        if cursor.fetchone():
            cursor.execute("DELETE FROM activity_log")
            
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='app_state'")
        if cursor.fetchone():
            cursor.execute("DELETE FROM app_state")
            
        conn.commit()
        print("✅ Databases are now empty.")
    except Exception as e:
        print(f"❌ Error during database cleanup: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def refine_cleaned_text(text):
    """Post-processes LLM output to split entries with multiple types or levels."""
    levels_set = {'A1', 'A2', 'B1', 'B2'}
    lines = text.split('\n')
    refined_lines = []
    
    for line in lines:
        if not line.strip(): continue
        
        # Split by comma
        parts = [p.strip() for p in line.split(',') if p.strip()]
        if not parts: continue
        
        word = parts[0]
        if word in levels_set: continue # Skip if word is just a level
        
        # Extract types and levels
        found_levels = []
        found_types = []
        
        for p in parts[1:]:
            # Check if this part is a level
            if p in levels_set:
                found_levels.append(p)
            else:
                # It's a type or multiple types (e.g., "adj/adv" or "prep. adv")
                # Split by common delimiters but keep multi-word types like "auxiliary v."
                if '/' in p:
                    sub_types = [t.strip() for t in p.split('/') if t.strip()]
                    found_types.extend(sub_types)
                elif '.' in p and len(p) <= 5: # e.g. "adv."
                    found_types.append(p.replace('.', ''))
                else:
                    found_types.append(p)
        
        # Try to find levels in the whole line if not found via comma split
        if not found_levels:
            found_levels = re.findall(r'\b(A1|A2|B1|B2)\b', line)
            
        if not found_levels: continue
        
        # If no types found, use 'n/a'
        if not found_types:
            found_types = ['n/a']
            
        # Deduplicate types while preserving order
        unique_types = []
        for t in found_types:
            if t not in unique_types and t not in levels_set:
                unique_types.append(t)
        
        if not unique_types: unique_types = ['n/a']

        # Splitting Logic
        if len(unique_types) > 1 and len(found_levels) == 1:
            # Case: one word, many types, one level -> repeat word and level
            for t in unique_types:
                refined_lines.append(f"{word}, {t}, {found_levels[0]}")
        elif len(unique_types) > 1 and len(found_levels) > 1:
            # Case: many types, many levels -> pair them
            for i in range(max(len(unique_types), len(found_levels))):
                t = unique_types[i] if i < len(unique_types) else unique_types[-1]
                l = found_levels[i] if i < len(found_levels) else found_levels[-1]
                refined_lines.append(f"{word}, {t}, {l}")
        else:
            # Standard case or fallback
            refined_lines.append(f"{word}, {unique_types[0]}, {found_levels[0]}")
            
    return "\n".join(refined_lines)

def clean_ocr_text():
    """Uses LLM to clean the messy OCR text into a perfect structured list."""
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: {INPUT_FILE} not found.")
        return False

    print("🧠 Using LLM to clean OCR noise and format data...")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # Chunk by characters to handle very long lines
    chunks = []
    start = 0
    while start < len(raw_text):
        end = start + 800
        if end >= len(raw_text):
            chunks.append(raw_text[start:])
            break
        # Find a good break point (space or newline)
        break_point = max(raw_text.rfind(' ', start, end), raw_text.rfind('\n', start, end))
        if break_point <= start:
            break_point = end
        chunks.append(raw_text[start:break_point])
        start = break_point

    clean_entries = []
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i + 1}/{len(chunks)}...")
        
        prompt = (
            "Review this messy OCR text from the Oxford 3000 list.\n"
            "Task: Extract vocabulary entries into a clean comma-separated list.\n"
            "Format: Each line MUST be exactly 'word, type, level'.\n"
            "Example Input: 'abandon v. B2 ability n. A2'\n"
            "Example Output:\nabandon, v, B2\nability, n, A2\n\n"
            "Instructions:\n"
            "1. IMPORTANT: Each entry must be on its OWN line. Do not combine multiple types into one line.\n"
            "2. If a word has multiple types (e.g. n. and v.), output TWO separate lines.\n"
            "3. Remove all headers, page numbers, copyright notices, and footer text.\n"
            "4. Output ONLY the list. No conversation, no explanations.\n"
            "5. If you see 'word, type1, type2, level', split it into 'word, type1, level' and 'word, type2, level'.\n\n"
            f"TEXT:\n{chunk}"
        )

        try:
            response = client.chat.completions.create(
                model="typhoon-v2.5-30b-a3b-instruct",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            content = response.choices[0].message.content.strip()
            # Apply robust refinement
            refined_chunk = refine_cleaned_text(content)
            clean_entries.append(refined_chunk)
        except Exception as e:
            print(f"Error cleaning chunk: {e}")

    final_text = "\n".join(clean_entries)
    with open(CLEAN_FILE, "w", encoding="utf-8") as f:
        f.write(final_text)
    print(f"✅ Cleaned text saved to {CLEAN_FILE}")
    return True

if __name__ == "__main__":
    # Ensure DB is initialized first
    init_db()
    
    clean_database()
    if clean_ocr_text():
        print("\n🚀 Starting ingestion...")
        with open(CLEAN_FILE, "r", encoding="utf-8") as f:
            cleaned_content = f.read()
        ingest_from_text(cleaned_content)
        print("\n✅ All done! Data is ready in practice.db")

