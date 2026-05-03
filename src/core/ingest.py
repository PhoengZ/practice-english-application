import sys
import os
import sqlite3
import argparse

# Ensure we can import from src when running from any directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from src.core.typhoon_utils import extract_text_from_pdf, translate_to_thai_batch, parse_oxford_ocr
from src.database.db_manager import DB_PATH

def ingest_from_text(ocr_text):
    """Ingests words directly from OCR text string."""
    # Parse lines: 'word, type, level'
    entries = []
    lines = ocr_text.split('\n')
    word_type_pairs = []
    
    for line in lines:
        parts = [p.strip() for p in line.split(',') if p.strip()]
        if len(parts) >= 3:
            word, w_type, level = parts[0], parts[1], parts[2]
            entries.append((word, w_type, level))
            word_type_pairs.append((word, w_type))
            
    if not entries:
        print("No words identified in the provided text.")
        return

    print(f"Identified {len(entries)} vocabulary entries.")
    
    # 2. Translate (word, type) pairs in batches
    translations = translate_to_thai_batch(word_type_pairs)

    # 3. Save to DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    count = 0
    for eng, w_type, level in entries:
        # Match using composite key
        thai = translations.get(f"{eng}|{w_type}", "")
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO words (english_word, word_type, word_level, thai_translation) VALUES (?, ?, ?, ?)", 
                (eng, w_type, level, thai)
            )
            if cursor.rowcount > 0:
                count += 1
        except Exception as e:
            print(f"Error inserting {eng}: {e}")
            
    conn.commit()
    conn.close()
    print(f"Successfully ingested {count} new entries into the database.")

def ingest_pdf(pdf_path):
    # In a real scenario, we'd use Typhoon OCR on the file
    print("For this demonstration, please provide the OCR text using the --text flag.")
    print("Example: python ingest.py --text \"abandon v. B2\"")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest English vocabulary using Typhoon.")
    parser.add_argument("--pdf", help="Path to the PDF file")
    parser.add_argument("--text", help="Direct OCR text input")
    parser.add_argument("--file", help="Path to a text file containing OCR text")
    args = parser.parse_args()
    
    if args.text:
        ingest_from_text(args.text)
    elif args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            ingest_from_text(f.read())
    elif args.pdf:
        ingest_pdf(args.pdf)
    else:
        parser.print_help()
