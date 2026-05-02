import os
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

TYPHOON_API_KEY = os.getenv("TYPHOON_API_KEY")
BASE_URL = "https://api.opentyphoon.ai/v1"

client = OpenAI(api_key=TYPHOON_API_KEY, base_url=BASE_URL)

def translate_to_thai_batch(english_words, batch_size=50):
    """Translates English words to Thai in batches to avoid truncation."""
    if not TYPHOON_API_KEY:
        print("Warning: TYPHOON_API_KEY not found. Using mock translations.")
        return {word: f"ไทย-{word}" for word in english_words}

    all_translations = {}
    
    for i in range(0, len(english_words), batch_size):
        batch = english_words[i:i + batch_size]
        print(f"Translating batch {i//batch_size + 1} ({len(batch)} words)...")
        
        prompt = f"Translate these English words to Thai (one per line, only the Thai word):\n" + "\n".join(batch)
        
        try:
            response = client.chat.completions.create(
                model="typhoon-v2.5-30b-a3b-instruct",
                messages=[
                    {"role": "system", "content": "You are an English-to-Thai translator. Output exactly one Thai translation per line. No English, no explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            thai_lines = [line.strip() for line in response.choices[0].message.content.strip().split('\n') if line.strip()]
            
            # Match back to English words
            for eng, thai in zip(batch, thai_lines):
                all_translations[eng] = thai
        except Exception as e:
            print(f"Batch translation error at index {i}: {e}")
            
    return all_translations

def parse_oxford_ocr(text):
    """
    Parses the Oxford 3000 OCR text in 'word, type, level' format.
    """
    words = []
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Split by comma and take the first part (the word)
        parts = line.split(',')
        if parts:
            word = parts[0].strip()
            # Basic validation: ensure it's not just a header or empty
            if word and not word.startswith('©') and not word.startswith('The Oxford'):
                if word not in words:
                    words.append(word)
    return words

def extract_text_from_pdf(pdf_path):
    """
    Uses Typhoon OCR VLM to extract text from a PDF.
    (Requires typhoon-ocr or vision API)
    """
    print(f"In a real setup, this would use Typhoon Vision API to OCR: {pdf_path}")
    # Since you provided the OCR text, we will use the parser on that content.
    return []
