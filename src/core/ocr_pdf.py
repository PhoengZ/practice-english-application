import os
import base64
import io
from PIL import Image
from pdf2image import convert_from_path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

TYPHOON_API_KEY = os.getenv("TYPHOON_API_KEY")
client = OpenAI(api_key=TYPHOON_API_KEY, base_url="https://api.opentyphoon.ai/v1")

def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def ocr_pdf_to_file(pdf_path, output_txt):
    print(f"Converting {pdf_path} to images...")
    # Requires poppler installed on Windows: https://github.com/oschwartz10612/poppler-windows/releases
    pages = convert_from_path(pdf_path, 300) 
    
    with open(output_txt, "w", encoding="utf-8") as f:
        for i, page in enumerate(pages):
            print(f"Processing Page {i+1}/{len(pages)}...")
            base64_image = encode_image(page)
            
            response = client.chat.completions.create(
                model="typhoon-ocr",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text", 
                                "text": "Extract all vocabulary entries from this document page. "
                                        "For each entry, format it exactly as: word, type, level. "
                                        "Example: abandon, v., B2. "
                                        "Only output the comma-separated list, one per line."
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                            },
                        ],
                    }
                ],
                max_tokens=2048
            )
            
            content = response.choices[0].message.content
            f.write(content + "\n")
            print(f"Page {i+1} completed.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python ocr_pdf.py <path_to_pdf>")
    else:
        ocr_pdf_to_file(sys.argv[1], "oxford.txt")
        print("Done! OCR results saved in oxford.txt")
