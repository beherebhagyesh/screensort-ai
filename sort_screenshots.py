import os
import shutil
import pytesseract
import time
import logging
import sys
import sqlite3
import re
import base64
from PIL import Image, ImageEnhance
from datetime import datetime

# Configuration
SOURCE_DIR = "/sdcard/Pictures/Screenshots"
DB_FILE = "screenshots.db"

# AI Configuration
AI_ENABLED = os.environ.get('SCREENSORT_AI', '0') == '1'
MODEL_PATH = "models/moondream2-text-model-f16.gguf"
MMPROJ_PATH = "models/moondream2-mmproj-f16.gguf"

# Global LLM instance (lazy loaded)
_llm_instance = None

CATEGORIES = {
    "Finance": ["bank", "pay", "rs", "transaction", "payment", "fund", "debit", "credit", "balance", "wallet", "upi", "amount", "currency", "invest"],
    "Chats": ["message", "typing", "online", "last seen", "whatsapp", "telegram", "chat", "dm", "reply", "sent"],
    "Shopping": ["cart", "order", "buy", "price", "discount", "offer", "delivery", "amazon", "flipkart", "myntra", "shop"],
    "Code": ["error", "bug", "code", "exception", "console", "terminal", "debug", "java", "python", "function", "class", "import", "const", "var"],
    "Social": ["post", "like", "comment", "share", "instagram", "facebook", "twitter", "meme", "video", "reel", "story", "feed"],
    "System": ["settings", "battery", "wifi", "bluetooth", "about device", "storage", "update", "notification"],
    "Events": ["ticket", "booking", "movie", "show", "date", "venue", "stadium", "concert", "event"],
    "Food": ["cook", "recipe", "ingredients", "food", "meal", "dish", "restaurant", "menu"],
    "Travel": ["map", "location", "navigate", "direction", "trip", "uber", "ola", "ride"]
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
        processed_at INTEGER,
        ai_category TEXT,
        ai_summary TEXT,
        ai_processed_at INTEGER
    )''')
    # Add new columns to existing tables (migration for existing DBs)
    for col, coltype in [('ai_category', 'TEXT'), ('ai_summary', 'TEXT'), ('ai_processed_at', 'INTEGER')]:
        try:
            c.execute(f'ALTER TABLE screenshots ADD COLUMN {col} {coltype}')
        except sqlite3.OperationalError:
            pass  # Column already exists
    conn.commit()
    return conn

def get_llm():
    """Lazy-load the Moondream2 LLM. Returns None if AI is disabled or model unavailable."""
    global _llm_instance
    if not AI_ENABLED:
        return None
    if _llm_instance is not None:
        return _llm_instance
    if not os.path.exists(MODEL_PATH):
        logging.warning(f"AI model not found at {MODEL_PATH}. Run download_model.py first.")
        return None
    try:
        from llama_cpp import Llama
        from llama_cpp.llama_chat_format import MoondreamChatHandler
        logging.info("Loading Moondream2 Model... (This may take a moment)")
        chat_handler = MoondreamChatHandler(clip_model_path=MMPROJ_PATH)
        _llm_instance = Llama(
            model_path=MODEL_PATH,
            chat_handler=chat_handler,
            n_ctx=2048,
            n_gpu_layers=0,
            verbose=False
        )
        logging.info("Moondream2 loaded successfully.")
        return _llm_instance
    except ImportError:
        logging.warning("llama-cpp-python not installed. AI features disabled.")
        return None
    except Exception as e:
        logging.error(f"Failed to load LLM: {e}")
        return None

def analyze_image_ai(image_path):
    """Use Moondream2 to visually analyze an image. Returns (category, summary) or (None, None)."""
    llm = get_llm()
    if llm is None:
        return None, None

    try:
        # Convert image to base64 data URI
        with open(image_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode('utf-8')
        ext = os.path.splitext(image_path)[1].lower().replace('.', '')
        if ext == 'jpg':
            ext = 'jpeg'
        data_uri = f"data:image/{ext};base64,{encoded}"

        # Categories match CATEGORIES dict keys
        valid_cats = list(CATEGORIES.keys()) + ["Unsorted"]
        cat_list = ", ".join(valid_cats)

        messages = [
            {"role": "system", "content": "You are a helpful assistant that categorizes and describes screenshots."},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": data_uri}},
                {"type": "text", "text": f"Analyze this image. First, provide a single word Category from this list: [{cat_list}]. Then, provide a one-sentence summary of the content. Format: 'Category: <Category> | Summary: <Summary>'"}
            ]}
        ]

        response = llm.create_chat_completion(messages=messages, max_tokens=100)
        content = response["choices"][0]["message"]["content"]

        # Parse response
        if "Category:" in content:
            category = content.split("Category:")[1].split("|")[0].strip()
            # Validate category
            if category not in valid_cats:
                category = "Unsorted"
            summary = content.split("Summary:")[1].strip() if "Summary:" in content else content
        else:
            category = "Unsorted"
            summary = content

        return category, summary
    except Exception as e:
        logging.error(f"AI analysis failed for {image_path}: {e}")
        return None, None

def extract_amount(text):
    """Find the first dollar or rupee amount in the text."""
    # Matches $10.99, £50, €100, Rs 500, ₹1,000.50, etc.
    # Uses non-capturing group for currency prefix, captures number in group(1)
    match = re.search(r'(?:[\$£€₹]\s*|Rs\.?\s*)(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)', text, re.IGNORECASE)
    if match:
        try:
            # Clean up the number string (remove commas)
            num_str = match.group(1).replace(',', '')
            return float(num_str)
        except (AttributeError, ValueError):
            return None
    return None

def preprocess_image(img):
    """
    Apply image processing to improve OCR accuracy.
    1. Convert to Grayscale
    2. Upscale (helps with small text)
    3. Increase Contrast and Sharpness
    """
    try:
        # 1. Grayscale
        img = img.convert('L')
        
        # 2. Upscale (2x)
        # Resize only if image is small-ish (optional, but good for speed vs quality trade-off)
        width, height = img.size
        new_size = (width * 2, height * 2)
        img = img.resize(new_size, Image.Resampling.BICUBIC)
        
        # 3. Enhance Contrast (makes text pop against bg)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        
        # 4. Sharpen (defines edges)
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(2.0)
        
        return img
    except Exception as e:
        logging.warning(f"Preprocessing failed: {e}")
        return img # Return original if enhancement fails

def categorize_image(image_path):
    try:
        # Check extension first
        ext = os.path.splitext(image_path)[1].lower()
        if ext in ['.mp4', '.mov', '.avi', '.mkv']:
            return "Videos", None, None

        img = Image.open(image_path)
        
        # --- NEW: Preprocess for better OCR ---
        processed_img = preprocess_image(img)
        
        text = pytesseract.image_to_string(processed_img).lower()
        
        # Extract Amount (using the original text or processed? Processed is usually better)
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
        # Log as warning, not error, to avoid panic
        logging.warning(f"Could not process image {image_path}: {e}")
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

            # OCR-based categorization
            category, text, amount = categorize_image(file_path)

            # AI-based categorization (if enabled)
            ai_category, ai_summary = None, None
            if AI_ENABLED and category != "Videos":
                logging.info(f"Running AI analysis on {filename}...")
                ai_category, ai_summary = analyze_image_ai(file_path)
                if ai_category:
                    logging.info(f"AI categorized as: {ai_category}")

            if category:
                # Use AI category if OCR couldn't determine (Unsorted) and AI succeeded
                effective_category = category
                if category == "Unsorted" and ai_category and ai_category != "Unsorted":
                    effective_category = ai_category
                    logging.info(f"Using AI category: {effective_category}")

                # Move logic: Only move if it's currently in the SOURCE_DIR root
                final_path = file_path
                current_dir_name = os.path.basename(os.path.dirname(file_path))

                # If file is in root OR in 'Unsorted' but now has a better category
                if directory == SOURCE_DIR or (current_dir_name == "Unsorted" and effective_category != "Unsorted"):
                     dest_dir = os.path.join(SOURCE_DIR, effective_category)
                     os.makedirs(dest_dir, exist_ok=True)
                     new_path = os.path.join(dest_dir, filename)
                     try:
                         shutil.move(file_path, new_path)
                         final_path = new_path
                         logging.info(f"Moved {filename} to {effective_category}")
                     except Exception as e:
                         logging.error(f"Failed to move {filename}: {e}")

                # Insert into DB (including AI fields)
                try:
                    created_at = int(os.path.getmtime(final_path) * 1000)
                    now_ms = int(time.time() * 1000)
                    cursor.execute('''INSERT INTO screenshots
                        (filename, path, category, text, amount, created_at, processed_at, ai_category, ai_summary, ai_processed_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (filename, final_path, effective_category, text, amount, created_at, now_ms,
                         ai_category, ai_summary, now_ms if ai_category else None))
                    conn.commit()
                    files_processed_count += 1
                except Exception as e:
                    logging.error(f"DB Error for {filename}: {e}")

    if files_processed_count > 0:
        logging.info(f"Batch complete. Indexed {files_processed_count} files.")

def process_ai_backfill(conn, limit=10):
    """Process existing DB entries that don't have AI analysis yet."""
    if not AI_ENABLED:
        return
    cursor = conn.cursor()
    cursor.execute('''SELECT id, filename, path FROM screenshots
                      WHERE ai_processed_at IS NULL AND category != 'Videos'
                      LIMIT ?''', (limit,))
    rows = cursor.fetchall()
    if not rows:
        return

    logging.info(f"AI backfill: {len(rows)} files to process")
    for row_id, filename, path in rows:
        if not os.path.exists(path):
            logging.warning(f"File missing for backfill: {path}")
            continue
        logging.info(f"AI backfill: {filename}")
        ai_category, ai_summary = analyze_image_ai(path)
        now_ms = int(time.time() * 1000)
        cursor.execute('''UPDATE screenshots SET ai_category=?, ai_summary=?, ai_processed_at=? WHERE id=?''',
                       (ai_category, ai_summary, now_ms, row_id))
        conn.commit()
    logging.info("AI backfill batch complete.")

def run_continuous(interval=60):
    conn = init_db()
    ai_status = "enabled" if AI_ENABLED else "disabled"
    logging.info(f"Starting Smart Indexer. AI: {ai_status}. Checking every {interval} seconds.")
    try:
        while True:
            process_files(conn)
            # Run AI backfill for existing files (process a few each cycle)
            if AI_ENABLED:
                process_ai_backfill(conn, limit=3)
            time.sleep(interval)
    except KeyboardInterrupt:
        logging.info("Stopping...")
        conn.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Screenshot Sorter with optional AI")
    parser.add_argument('--ai', action='store_true', help='Enable Moondream2 AI analysis')
    parser.add_argument('--interval', type=int, default=60, help='Scan interval in seconds')
    args = parser.parse_args()

    if args.ai:
        AI_ENABLED = True
    run_continuous(interval=args.interval)