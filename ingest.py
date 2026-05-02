import sys
import sqlite3
import argparse
from typhoon_utils import extract_text_from_pdf, translate_to_thai
from db_manager import DB_PATH

def ingest_pdf(pdf_path):
    # 1. Extract
    eng_words = extract_text_from_pdf(pdf_path)
    if not eng_words:
        print("No words found in PDF.")
        return

    # 2. Translate
    print(f"Translating {len(eng_words)} words...")
    translations = translate_to_thai(eng_words)

    # 3. Save to DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    count = 0
    for eng, thai in translations.items():
        try:
            cursor.execute("INSERT OR IGNORE INTO words (english_word, thai_translation) VALUES (?, ?)", (eng, thai))
            if cursor.rowcount > 0:
                count += 1
        except Exception as e:
            print(f"Error saving {eng}: {e}")
            
    conn.commit()
    conn.close()
    print(f"Successfully ingested {count} new words into the database.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest English vocabulary from PDF using Typhoon.")
    parser.add_argument("pdf", help="Path to the PDF file")
    args = parser.parse_args()
    
    ingest_pdf(args.pdf)
