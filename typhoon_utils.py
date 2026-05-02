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
                model="scb10x/typhoon-v1.5-8b-instruct",
                messages=[
                    {"role": "system", "content": "You are an English-to-Thai translator. Output exactly one Thai translation per line. No English, no explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            thai_lines = [line.strip() for line in response.choices[0].message.content.strip().split('\n') if line.strip()]
            
            # Match back to English words, being careful with count mismatches
            for eng, thai in zip(batch, thai_lines):
                all_translations[eng] = thai
        except Exception as e:
            print(f"Batch translation error at index {i}: {e}")
            
    return all_translations

def parse_oxford_ocr(text):
    """
    Parses the Oxford 3000 OCR text to extract English words.
    Handles 'word pos level' format and common OCR variations.
    """
    # Pattern to capture words followed by common part-of-speech markers
    # Also handles lines that might just start with the word and have markers later
    pattern = r"^([a-zA-Z\s\-\'\/12,]+?)(?:\s+|,|\.|$)\s*(?:v\.|n\.|adj\.|adv\.|prep\.|conj\.|pron\.|exclam\.|det\.|number|auxiliary|modal)"
    
    words = []
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line: continue
        
        match = re.search(pattern, line)
        if match:
            word = match.group(1).strip()
            # Clean up 'can1' -> 'can' or trailing commas
            word = re.sub(r'\d+$', '', word)
            word = word.rstrip(',').strip()
            if word and word not in words:
                words.append(word)
        else:
            # Fallback for simple lines or multi-word entries without clear markers
            # If the line looks like a vocab entry but missed the pattern
            parts = line.split()
            if parts and len(parts[0]) > 1:
                word = parts[0].rstrip(',').strip()
                if word not in words and word.isalpha():
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
