import os
import sqlite3
import re
from openai import OpenAI
from dotenv import load_dotenv
from ingest import ingest_from_text

load_dotenv()

DB_PATH = "practice.db"
INPUT_FILE = "oxford.txt"
CLEAN_FILE = "oxford_clean.txt"
TYPHOON_API_KEY = os.getenv("TYPHOON_API_KEY")

client = OpenAI(api_key=TYPHOON_API_KEY, base_url="https://api.opentyphoon.ai/v1")

def clean_database():
    """Wipes the database tables to start fresh."""
    print("🧹 Cleaning database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Check if tables exist before deleting
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
    conn.close()
    print("✅ Database is now empty.")

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
            "Format: Each line must be exactly 'word, type, level'.\n"
            "Example Input: 'abandon v. B2 ability n. A2'\n"
            "Example Output:\nabandon, v, B2\nability, n, A2\n\n"
            "Instructions:\n"
            "1. Remove all headers, page numbers, copyright notices, and footer text.\n"
            "2. Fix entries where multiple words are on one line.\n"
            "3. Output ONLY the list. No conversation, no explanations.\n"
            "4. Ensure the order is exactly: word, type, level.\n\n"
            f"TEXT:\n{chunk}"
        )

        try:
            response = client.chat.completions.create(
                model="typhoon-v2.5-30b-a3b-instruct",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            content = response.choices[0].message.content.strip()
            # Basic filtering to ensure we only get lines with commas
            valid_lines = [l for l in content.split('\n') if ',' in l]
            clean_entries.append("\n".join(valid_lines))
        except Exception as e:
            print(f"Error cleaning chunk: {e}")

    final_text = "\n".join(clean_entries)
    with open(CLEAN_FILE, "w", encoding="utf-8") as f:
        f.write(final_text)
    print(f"✅ Cleaned text saved to {CLEAN_FILE}")
    return True

if __name__ == "__main__":
    # Ensure DB is initialized first
    from db_manager import init_db
    init_db()
    
    clean_database()
    if clean_ocr_text():
        print("\n🚀 Starting ingestion...")
        with open(CLEAN_FILE, "r", encoding="utf-8") as f:
            cleaned_content = f.read()
        ingest_from_text(cleaned_content)
        print("\n✅ All done! Data is ready in practice.db")

