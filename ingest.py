import sys
import sqlite3
import argparse
from typhoon_utils import extract_text_from_pdf, translate_to_thai_batch, parse_oxford_ocr
from db_manager import DB_PATH

def ingest_from_text(ocr_text):
    """Ingests words directly from OCR text string."""
    eng_words = parse_oxford_ocr(ocr_text)
    if not eng_words:
        print("No words identified in the provided text.")
        return

    print(f"Identified {len(eng_words)} unique English words.")
    
    # 2. Translate in batches
    translations = translate_to_thai_batch(eng_words)

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
            pass
            
    conn.commit()
    conn.close()
    print(f"Successfully ingested {count} new words into the database.")

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
