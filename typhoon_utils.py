import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

TYPHOON_API_KEY = os.getenv("TYPHOON_API_KEY")
BASE_URL = "https://api.opentyphoon.ai/v1"

client = OpenAI(api_key=TYPHOON_API_KEY, base_url=BASE_URL)

def translate_to_thai(english_words):
    """Translates a list of English words to Thai using Typhoon Translate."""
    if not TYPHOON_API_KEY:
        print("Warning: TYPHOON_API_KEY not found. Using mock translations.")
        return {word: f"ไทย-{word}" for word in english_words}

    prompt = f"Translate the following English words to Thai, one per line:\n" + "\n".join(english_words)
    
    try:
        response = client.chat.completions.create(
            model="scb10x/typhoon-v1.5-8b-instruct", # Or latest translation model
            messages=[
                {"role": "system", "content": "You are a professional English-to-Thai translator. Provide only the Thai word translations, one per line."},
                {"role": "user", "content": prompt}
            ]
        )
        translations = response.choices[0].message.content.strip().split('\n')
        return dict(zip(english_words, [t.strip() for t in translations]))
    except Exception as e:
        print(f"Translation error: {e}")
        return {}

def extract_text_from_pdf(pdf_path):
    """
    Placeholder for Typhoon OCR integration.
    Actual implementation would use the typhoon-ocr package or API.
    """
    # For now, we simulate extraction or use a simple PDF text extractor if available
    # In a real scenario, we'd send the PDF to Typhoon OCR API
    print(f"Extracting text from {pdf_path} using Typhoon OCR...")
    # Mocking extracted words
    return ["Artificial Intelligence", "Machine Learning", "Database", "Algorithm", "Architecture"]
