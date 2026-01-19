import os
import shutil
import pytesseract
import time
import logging
import sys
import sqlite3
import re
from PIL import Image
from datetime import datetime

# Configuration
SOURCE_DIR = "/sdcard/Pictures/Screenshots"
DB_FILE = "screenshots.db"

CATEGORIES = {
    "Finance": ["bank", "pay", "rs", "transaction", "payment", "fund", "debit", "credit", "balance", "wallet", "upi", "amount", "currency", "invest"],
    "Chats": ["message", "typing", "online", "last seen", "whatsapp", "telegram", "chat", "dm", "reply", "sent"],
    "Shopping": ["cart", "order", "buy", "price", "discount", "offer", "delivery", "amazon", "flipkart", "myntra", "shop"],
    "Code_Tech": ["error", "bug", "code", "exception", "console", "terminal", "debug", "java", "python", "function", "class", "import", "const", "var"],
    "Social_Media": ["post", "like", "comment", "share", "instagram", "facebook", "twitter", "meme", "video", "reel", "story", "feed"],
    "System": ["settings", "battery", "wifi", "bluetooth", "about device", "storage", "update", "notification"],
    "Events": ["ticket", "booking", "movie", "show", "date", "venue", "stadium", "concert", "event"],
    "Food": ["cook", "recipe", "ingredients", "food", "meal", "dish", "restaurant", "menu"],
    "Maps_Travel": ["map", "location", "navigate", "direction", "trip", "uber", "ola", "ride"]
}

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def init_db():
    """Initialize the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS screenshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT UNIQUE,
        path TEXT,
        category TEXT,
        text TEXT,
        amount REAL,
        created_at INTEGER,
        processed_at INTEGER
    )''')
    conn.commit()
    return conn

def extract_amount(text):
    """Find the first dollar or rupee amount in the text."""
    # Matches $10.99, $ 10.99, Rs 500, etc.
    match = re.search(r'[\$£€]|Rs\.?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text, re.IGNORECASE)
    if match:
        try:
            # Clean up the number string (remove commas)
            num_str = match.group(1).replace(',', '')
            return float(num_str)
        except:
            return None
    
    # Fallback for simple numbers with decimals if currency symbol is missed but context implies it? 
    # Keeping it strict for now to avoid false positives (like version numbers).
    return None

def categorize_image(image_path):
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img).lower()
        
        # Extract Amount
        amount = extract_amount(text)
        
        # Determine Category
        best_category = "Unsorted"
        for category, keywords in CATEGORIES.items():
            for keyword in keywords:
                if keyword in text:
                    best_category = category
                    break
            if best_category != "Unsorted":
                break
        
        return best_category, text, amount
    except Exception as e:
        logging.error(f"Error processing {image_path}: {e}")
        return None, None, None

def process_files(conn):
    logging.info("Scanning for screenshots...")
    cursor = conn.cursor()
    
    # 1. Scan Root Folder (New Files)
    # 2. Scan Category Folders (Existing Files that might not be in DB)
    
    dirs_to_scan = [SOURCE_DIR] + [os.path.join(SOURCE_DIR, cat) for cat in CATEGORIES.keys()] + [os.path.join(SOURCE_DIR, "Unsorted")]
    
    files_processed_count = 0
    
    for directory in dirs_to_scan:
        if not os.path.exists(directory):
            continue
            
        files = os.listdir(directory)
        
        for filename in files:
            if filename.startswith("."): continue
            
            # Basic extension check
            ext = os.path.splitext(filename)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.mp4']:
                continue

            # Check if already in DB
            cursor.execute("SELECT id FROM screenshots WHERE filename = ?", (filename,))
            if cursor.fetchone():
                continue # Skip processing
            
            file_path = os.path.join(directory, filename)
            if not os.path.isfile(file_path): 
                continue

            logging.info(f"Processing new file: {filename}")
            
            # Process
            category, text, amount = categorize_image(file_path)
            
            if category:
                # Move logic: Only move if it's currently in the SOURCE_DIR root
                # If it's already in a subdir, just update the path in our record
                
                final_path = file_path
                current_dir_name = os.path.basename(os.path.dirname(file_path))
                
                # If file is in root OR in 'Unsorted' but now has a better category
                if directory == SOURCE_DIR or (current_dir_name == "Unsorted" and category != "Unsorted"):
                     dest_dir = os.path.join(SOURCE_DIR, category)
                     os.makedirs(dest_dir, exist_ok=True)
                     new_path = os.path.join(dest_dir, filename)
                     try:
                         shutil.move(file_path, new_path)
                         final_path = new_path
                         logging.info(f"Moved {filename} to {category}")
                     except Exception as e:
                         logging.error(f"Failed to move {filename}: {e}")
                
                # Insert into DB
                try:
                    created_at = int(os.path.getmtime(final_path) * 1000)
                    cursor.execute('''INSERT INTO screenshots 
                        (filename, path, category, text, amount, created_at, processed_at) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                        (filename, final_path, category, text, amount, created_at, int(time.time() * 1000)))
                    conn.commit()
                    files_processed_count += 1
                except Exception as e:
                    logging.error(f"DB Error for {filename}: {e}")

    if files_processed_count > 0:
        logging.info(f"Batch complete. Indexed {files_processed_count} files.")

def run_continuous(interval=60):
    conn = init_db()
    logging.info(f"Starting Smart Indexer. Checking every {interval} seconds.")
    try:
        while True:
            process_files(conn)
            time.sleep(interval)
    except KeyboardInterrupt:
        logging.info("Stopping...")
        conn.close()

if __name__ == "__main__":
    run_continuous()