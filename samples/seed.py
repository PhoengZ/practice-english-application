import sqlite3
from db_manager import DB_PATH

def populate_sample():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    sample_words = [
        ("Apple", "แอปเปิ้ล"),
        ("Banana", "กล้วย"),
        ("Cat", "แมว"),
        ("Dog", "สุนัข"),
        ("Elephant", "ช้าง"),
        ("Flower", "ดอกไม้"),
        ("Green", "สีเขียว"),
        ("House", "บ้าน"),
        ("Ice", "น้ำแข็ง"),
        ("Juice", "น้ำผลไม้"),
        ("King", "พระราชา"),
        ("Lamp", "ตะเกียง"),
        ("Mountain", "ภูเขา")
    ]
    cursor.executemany("INSERT OR IGNORE INTO words (english_word, thai_translation) VALUES (?, ?)", sample_words)
    conn.commit()
    conn.close()
    print("Sample data populated.")

if __name__ == "__main__":
    populate_sample()
