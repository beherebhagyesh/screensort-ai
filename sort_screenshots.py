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

# Video Processing Configuration
VIDEO_ENABLED = os.environ.get('SCREENSORT_VIDEO', '0') == '1'
VIDEO_FRAME_INTERVAL = 5  # Extract frame every N seconds
VIDEO_MAX_FRAMES = 10     # Maximum frames to analyze per video

# Translation Configuration
TRANSLATION_ENABLED = os.environ.get('SCREENSORT_TRANSLATE', '0') == '1'
TARGET_LANGUAGE = 'en'  # Default target language

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
    migrations = [
        ('ai_category', 'TEXT'), ('ai_summary', 'TEXT'), ('ai_processed_at', 'INTEGER'),
        ('detected_language', 'TEXT'), ('translated_text', 'TEXT'),
        ('is_video', 'INTEGER'), ('video_frames_analyzed', 'INTEGER'), ('video_objects', 'TEXT')
    ]
    for col, coltype in migrations:
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

def extract_video_frames(video_path, interval=VIDEO_FRAME_INTERVAL, max_frames=VIDEO_MAX_FRAMES):
    """Extract frames from video at regular intervals. Returns list of PIL Images."""
    frames = []
    try:
        import cv2
    except ImportError:
        logging.warning("opencv-python not installed. Video analysis disabled. Install with: pip install opencv-python")
        return frames

    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logging.warning(f"Could not open video: {video_path}")
            return frames

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0

        logging.info(f"Video: {duration:.1f}s, {fps:.1f}fps, extracting frames every {interval}s")

        frame_indices = []
        for sec in range(0, int(duration), interval):
            frame_indices.append(int(sec * fps))
            if len(frame_indices) >= max_frames:
                break

        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                # Convert BGR to RGB and then to PIL Image
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame_rgb)
                frames.append(pil_img)

        cap.release()
        logging.info(f"Extracted {len(frames)} frames from video")
    except Exception as e:
        logging.error(f"Video frame extraction failed: {e}")

    return frames

def analyze_video_ai(video_path):
    """Analyze video by extracting frames and running AI on each. Returns aggregated results."""
    if not VIDEO_ENABLED or not AI_ENABLED:
        return None, None, 0

    frames = extract_video_frames(video_path)
    if not frames:
        return None, None, 0

    llm = get_llm()
    if llm is None:
        return None, None, 0

    all_objects = []
    categories_found = []
    summaries = []

    for i, frame in enumerate(frames):
        try:
            # Save frame temporarily for analysis
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                frame.save(tmp.name, 'JPEG')
                tmp_path = tmp.name

            # Analyze frame
            logging.info(f"Analyzing frame {i+1}/{len(frames)}...")

            # Convert to base64
            with open(tmp_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')
            data_uri = f"data:image/jpeg;base64,{encoded}"

            messages = [
                {"role": "system", "content": "You are an assistant that identifies objects and activities in video frames."},
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": data_uri}},
                    {"type": "text", "text": "List the main objects, people, and activities visible in this frame. Be concise, comma-separated."}
                ]}
            ]

            response = llm.create_chat_completion(messages=messages, max_tokens=80)
            content = response["choices"][0]["message"]["content"]
            all_objects.append(content)

            # Also get category
            cat, summary = analyze_image_ai(tmp_path)
            if cat:
                categories_found.append(cat)
            if summary:
                summaries.append(summary)

            os.unlink(tmp_path)
        except Exception as e:
            logging.error(f"Frame {i+1} analysis failed: {e}")

    # Aggregate results
    if categories_found:
        from collections import Counter
        most_common_cat = Counter(categories_found).most_common(1)[0][0]
    else:
        most_common_cat = "Videos"

    combined_objects = " | ".join(all_objects) if all_objects else None
    combined_summary = summaries[0] if summaries else None  # Use first frame's summary

    return most_common_cat, combined_summary, len(frames), combined_objects

def detect_language(text):
    """Detect the language of text. Returns language code or None."""
    if not text or len(text.strip()) < 10:
        return None
    try:
        from langdetect import detect, LangDetectException
        lang = detect(text)
        return lang
    except ImportError:
        logging.warning("langdetect not installed. Install with: pip install langdetect")
        return None
    except LangDetectException:
        return None
    except Exception as e:
        logging.error(f"Language detection failed: {e}")
        return None

def translate_text(text, source_lang=None, target_lang=TARGET_LANGUAGE):
    """Translate text to target language. Returns translated text or None."""
    if not TRANSLATION_ENABLED:
        return None
    if not text or len(text.strip()) < 5:
        return None
    if source_lang == target_lang:
        return None  # No translation needed

    try:
        from googletrans import Translator
        translator = Translator()
        result = translator.translate(text, src=source_lang or 'auto', dest=target_lang)
        return result.text
    except ImportError:
        logging.warning("googletrans not installed. Install with: pip install googletrans==4.0.0-rc1")
        return None
    except Exception as e:
        logging.error(f"Translation failed: {e}")
        return None

def process_text_translation(text):
    """Detect language and translate if not in target language. Returns (detected_lang, translated_text)."""
    if not TRANSLATION_ENABLED or not text:
        return None, None

    detected_lang = detect_language(text)
    if not detected_lang:
        return None, None

    logging.info(f"Detected language: {detected_lang}")

    if detected_lang == TARGET_LANGUAGE:
        return detected_lang, None  # Already in target language

    translated = translate_text(text, source_lang=detected_lang)
    if translated:
        logging.info(f"Translated from {detected_lang} to {TARGET_LANGUAGE}")
    return detected_lang, translated

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

def is_video_file(filepath):
    """Check if file is a video based on extension."""
    ext = os.path.splitext(filepath)[1].lower()
    return ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.3gp']

def categorize_image(image_path):
    try:
        # Check extension first
        if is_video_file(image_path):
            return "Videos", None, None, True

        img = Image.open(image_path)

        # --- Preprocess for better OCR ---
        processed_img = preprocess_image(img)

        text = pytesseract.image_to_string(processed_img).lower()

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

        return best_category, text, amount, False
    except Exception as e:
        logging.warning(f"Could not process image {image_path}: {e}")
        return None, None, None, False

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
            
            # Basic extension check (images and videos)
            ext = os.path.splitext(filename)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.mp4', '.mov', '.avi', '.mkv', '.webm', '.3gp']:
                continue

            # Check if already in DB
            cursor.execute("SELECT id FROM screenshots WHERE filename = ?", (filename,))
            if cursor.fetchone():
                continue # Skip processing
            
            file_path = os.path.join(directory, filename)
            if not os.path.isfile(file_path): 
                continue

            logging.info(f"Processing new file: {filename}")

            # OCR-based categorization (returns 4 values now)
            category, text, amount, is_video = categorize_image(file_path)

            # Initialize extended fields
            ai_category, ai_summary = None, None
            detected_lang, translated_text = None, None
            video_frames_analyzed, video_objects = 0, None

            if is_video and VIDEO_ENABLED:
                # Video frame-by-frame analysis
                logging.info(f"Running video analysis on {filename}...")
                vid_cat, vid_summary, vid_frames, vid_objects = analyze_video_ai(file_path)
                if vid_cat:
                    ai_category = vid_cat
                    ai_summary = vid_summary
                    video_frames_analyzed = vid_frames
                    video_objects = vid_objects
                    logging.info(f"Video analyzed: {vid_frames} frames, category: {vid_cat}")

            elif not is_video:
                # AI-based categorization for images
                if AI_ENABLED:
                    logging.info(f"Running AI analysis on {filename}...")
                    ai_category, ai_summary = analyze_image_ai(file_path)
                    if ai_category:
                        logging.info(f"AI categorized as: {ai_category}")

                # Translation (for images with OCR text)
                if TRANSLATION_ENABLED and text:
                    detected_lang, translated_text = process_text_translation(text)

            if category:
                # Use AI category if OCR couldn't determine (Unsorted) and AI succeeded
                effective_category = category
                if category == "Unsorted" and ai_category and ai_category != "Unsorted":
                    effective_category = ai_category
                    logging.info(f"Using AI category: {effective_category}")
                elif is_video and ai_category and ai_category != "Videos":
                    effective_category = ai_category  # Use AI category for videos too

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

                # Insert into DB (including all new fields)
                try:
                    created_at = int(os.path.getmtime(final_path) * 1000)
                    now_ms = int(time.time() * 1000)
                    cursor.execute('''INSERT INTO screenshots
                        (filename, path, category, text, amount, created_at, processed_at,
                         ai_category, ai_summary, ai_processed_at,
                         detected_language, translated_text, is_video, video_frames_analyzed, video_objects)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (filename, final_path, effective_category, text, amount, created_at, now_ms,
                         ai_category, ai_summary, now_ms if ai_category else None,
                         detected_lang, translated_text, 1 if is_video else 0, video_frames_analyzed, video_objects))
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
    features = []
    if AI_ENABLED:
        features.append("AI")
    if VIDEO_ENABLED:
        features.append("Video")
    if TRANSLATION_ENABLED:
        features.append(f"Translation→{TARGET_LANGUAGE}")
    status = ", ".join(features) if features else "basic OCR only"
    logging.info(f"Starting Smart Indexer. Features: {status}. Interval: {interval}s")
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
    parser = argparse.ArgumentParser(description="Screenshot Sorter with AI, Video Analysis & Translation")
    parser.add_argument('--ai', action='store_true', help='Enable Moondream2 AI analysis')
    parser.add_argument('--video', action='store_true', help='Enable video frame-by-frame analysis')
    parser.add_argument('--translate', action='store_true', help='Enable auto-translation of OCR text')
    parser.add_argument('--target-lang', type=str, default='en', help='Target language for translation (default: en)')
    parser.add_argument('--interval', type=int, default=60, help='Scan interval in seconds')
    args = parser.parse_args()

    if args.ai:
        AI_ENABLED = True
    if args.video:
        VIDEO_ENABLED = True
        AI_ENABLED = True  # Video analysis requires AI
    if args.translate:
        TRANSLATION_ENABLED = True
    if args.target_lang:
        TARGET_LANGUAGE = args.target_lang

    run_continuous(interval=args.interval)