import os
import shutil
import pytesseract
import time
import logging
import sys
from PIL import Image

# Configuration
SOURCE_DIR = "/sdcard/Pictures/Screenshots"
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

# Ensure category directories exist
for category in CATEGORIES:
    path = os.path.join(SOURCE_DIR, category)
    try:
        os.makedirs(path, exist_ok=True)
    except OSError as e:
        logging.error(f"Failed to create directory {path}: {e}")

# Create an 'Unsorted' directory for things that don't match
try:
    os.makedirs(os.path.join(SOURCE_DIR, "Unsorted"), exist_ok=True)
except OSError as e:
    logging.error(f"Failed to create Unsorted directory: {e}")

def categorize_image(image_path):
    try:
        # Open image
        img = Image.open(image_path)
        
        # Extract text
        text = pytesseract.image_to_string(img).lower()
        
        # Check keywords
        for category, keywords in CATEGORIES.items():
            for keyword in keywords:
                if keyword in text:
                    return category
        
        return "Unsorted"
    except Exception as e:
        logging.error(f"Error processing {image_path}: {e}")
        return None

def process_files():
    logging.info("Scanning for screenshots...")
    try:
        files = [f for f in os.listdir(SOURCE_DIR) if os.path.isfile(os.path.join(SOURCE_DIR, f))]
    except FileNotFoundError:
        logging.error(f"Source directory {SOURCE_DIR} not found.")
        return

    total_files = len(files)
    if total_files > 0:
        logging.info(f"Found {total_files} files to process.")
    
    processed_count = 0
    
    for filename in files:
        if filename.startswith("."): continue # Skip hidden files
        
        file_path = os.path.join(SOURCE_DIR, filename)
        
        category = categorize_image(file_path)
        
        if category:
            dest_dir = os.path.join(SOURCE_DIR, category)
            try:
                shutil.move(file_path, os.path.join(dest_dir, filename))
                logging.info(f"Moved {filename} to {category}")
            except Exception as e:
                logging.error(f"Failed to move {filename} to {category}: {e}")
        
        processed_count += 1
        if processed_count % 10 == 0:
            logging.info(f"Processed {processed_count}/{total_files}...")

    if processed_count > 0:
        logging.info(f"Batch complete. Processed {processed_count} files.")

def run_continuous(interval=60):
    logging.info(f"Starting continuous monitoring. Checking every {interval} seconds.")
    while True:
        process_files()
        time.sleep(interval)

def main():
    # By default, run continuously
    try:
        run_continuous()
    except KeyboardInterrupt:
        logging.info("Stopping screenshot organization.")

if __name__ == "__main__":
    main()