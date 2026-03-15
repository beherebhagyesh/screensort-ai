import sqlite3
import time
import random
from datetime import datetime, timedelta

DB_FILE = "screenshots.db"

def seed():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Create table if not exists (schema from sort_screenshots.py)
    c.execute('''CREATE TABLE IF NOT EXISTS screenshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT UNIQUE,
        path TEXT,
        category TEXT,
        text TEXT,
        amount REAL,
        created_at INTEGER,
        processed_at INTEGER,
        ai_category TEXT,
        ai_summary TEXT,
        ai_processed_at INTEGER,
        detected_language TEXT,
        translated_text TEXT,
        is_video INTEGER,
        video_frames_analyzed INTEGER,
        video_objects TEXT,
        ocr_method TEXT,
        ai_extracted_text TEXT
    )''')

    # Check if empty
    c.execute("SELECT count(*) FROM screenshots")
    if c.fetchone()[0] > 0:
        print("DB already has data. Skipping seed.")
        return

    print("Seeding database with mock data...")
    
    categories = ["Finance", "Chats", "Shopping", "Code", "Social", "System"]
    languages = ["en", "es", "hi", "fr"]
    
    # Generate data for past 14 days
    for i in range(50):
        days_ago = random.randint(0, 14)
        created_at = int((datetime.now() - timedelta(days=days_ago)).timestamp() * 1000)
        
        category = random.choice(categories)
        amount = None
        if category == "Finance" or category == "Shopping":
            if random.random() > 0.3:
                amount = round(random.uniform(10.0, 500.0), 2)
        
        is_video = 1 if random.random() > 0.9 else 0
        lang = random.choice(languages) if random.random() > 0.7 else None
        
        filename = f"screenshot_{created_at}_{i}.jpg"
        
        c.execute('''INSERT INTO screenshots
            (filename, path, category, text, amount, created_at, processed_at, 
             ai_category, ai_summary, detected_language, is_video)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (filename, f"/sdcard/Pictures/Screenshots/{category}/{filename}", 
             category, "Mock text content for demo purposes...", amount, 
             created_at, created_at + 1000, 
             category, f"A mock screenshot of {category}", lang, is_video)
        )

    conn.commit()
    print("Seeded 50 entries.")
    conn.close()

if __name__ == "__main__":
    seed()
