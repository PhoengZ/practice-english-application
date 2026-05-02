import os
import sqlite3
import re
from openai import OpenAI
from dotenv import load_dotenv

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
    cursor.execute("DELETE FROM words")
    cursor.execute("DELETE FROM activity_log")
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

    # Split into chunks to avoid token limits (approx 2 pages per chunk)
    lines = raw_text.split('\n')
    chunk_size = 200 
    clean_entries = []

    for i in range(0, len(lines), chunk_size):
        chunk = "\n".join(lines[i:i + chunk_size])
        print(f"Processing chunk {i//chunk_size + 1}...")
        
        prompt = (
            "Review this messy OCR text from the Oxford 3000 list. "
            "Remove headers, page numbers, copyright notice, and empty lines. "
            "Fix entries where multiple words are on one line. "
            "Output ONLY a clean list where each line is: 'word, type, level'. "
            "Ignore everything that is not a vocabulary entry.\n\n"
            f"TEXT:\n{chunk}"
        )

        try:
            response = client.chat.completions.create(
                model="typhoon-v2.5-30b-a3b-instruct",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            clean_entries.append(response.choices[0].message.content.strip())
        except Exception as e:
            print(f"Error cleaning chunk: {e}")

    final_text = "\n".join(clean_entries)
    with open(CLEAN_FILE, "w", encoding="utf-8") as f:
        f.write(final_text)
    print(f"✅ Cleaned text saved to {CLEAN_FILE}")
    return True

if __name__ == "__main__":
    clean_database()
    if clean_ocr_text():
        print("\n🚀 Next step: Run 'python ingest.py --file oxford_clean.txt' to re-import the perfect data.")
