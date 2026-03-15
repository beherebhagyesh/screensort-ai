"""
DEPRECATED: This standalone script has been integrated into sort_screenshots.py

Use instead:
    python sort_screenshots.py --ai

This file is kept for reference and backward compatibility with the
knowledge_base markdown output format. For database-integrated AI
processing, use the main sort_screenshots.py with --ai flag.
"""
import os
import sys
import logging
import json
import re
from datetime import datetime
import pytesseract
from PIL import Image

# LLM Imports
from llama_cpp import Llama
from llama_cpp.llama_chat_format import MoondreamChatHandler

# Configuration
# Directories to scan for text-rich images
SOURCE_DIRS = [
    "/sdcard/Pictures/Screenshots",
    "/sdcard/Download",
    "/sdcard/WhatsApp/Media/WhatsApp Images",
    "/sdcard/Pictures/Twitter",
    "/sdcard/Pictures/Instagram"
]

KB_DIR = "knowledge_base"  # Output directory for the docs
MODEL_PATH = "models/moondream2-text-model-f16.gguf"
MMPROJ_PATH = "models/moondream2-mmproj-f16.gguf"
LIMIT = 10  # Increased limit for broader scan

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_llm():
    if not os.path.exists(MODEL_PATH):
        logging.error(f"Model not found at {MODEL_PATH}. Please run download_model.py first.")
        sys.exit(1)
        
    logging.info("Loading Moondream2 Model... (This may take a moment)")
    try:
        chat_handler = MoondreamChatHandler(clip_model_path=MMPROJ_PATH)
        llm = Llama(
            model_path=MODEL_PATH,
            chat_handler=chat_handler,
            n_ctx=2048,
            n_gpu_layers=0, # CPU only
            verbose=False
        )
        return llm
    except Exception as e:
        logging.error(f"Failed to load LLM: {e}")
        sys.exit(1)

def analyze_image(llm, image_path):
    # 1. Visual Analysis
    logging.info(f"Analyzing visual content of {os.path.basename(image_path)}...")
    
    import base64
    def image_to_base64_data_uri(path):
        with open(path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            ext = os.path.splitext(path)[1].lower().replace('.', '')
            if ext == 'jpg': ext = 'jpeg'
            return f"data:image/{ext};base64,{encoded_string}"

    try:
        data_uri = image_to_base64_data_uri(image_path)
        
        # Focused prompt for categorization - categories match sort_screenshots.py
        messages = [
            {"role": "system", "content": "You are a helpful assistant that categorizes and describes screenshots."},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": data_uri}},
                {"type": "text", "text": "Analyze this image. First, provide a single word Category from this list: [Finance, Chats, Shopping, Code, Social, System, Events, Food, Travel, Unsorted]. Then, provide a one-sentence summary of the content. Format: 'Category: <Category> | Summary: <Summary>'"}
            ]}
        ]
        
        response = llm.create_chat_completion(messages=messages, max_tokens=100)
        content = response["choices"][0]["message"]["content"]
        
        # Parse result
        if "Category:" in content:
            category = content.split("Category:")[1].split("|")[0].strip()
            summary = content.split("Summary:")[1].strip() if "Summary:" in content else content
        else:
            category = "Unsorted"
            summary = content
            
    except Exception as e:
        logging.error(f"LLM analysis failed: {e}")
        category = "Error"
        summary = "Analysis Failed"

    # 2. OCR Analysis
    # logging.info("Extracting text...")
    try:
        text = pytesseract.image_to_string(Image.open(image_path)).strip()
    except Exception as e:
        text = f"OCR Failed: {e}"
        
    return category, summary, text

def update_knowledge_base(item):
    """Appends the analyzed item to the specific category markdown file."""
    if not os.path.exists(KB_DIR):
        os.makedirs(KB_DIR)
        
    # Sanitize category filename
    safe_cat = "".join([c for c in item['category'] if c.isalnum() or c in (' ', '_')]).strip().replace(' ', '_')
    if not safe_cat: safe_cat = "Unsorted"
    
    filename = os.path.join(KB_DIR, f"{safe_cat}.md")
    
    # Init file if new
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            f.write(f"# Knowledge Base: {safe_cat}\n\n")

    with open(filename, "a") as f:
        f.write(f"## {item['filename']}\n")
        f.write(f"**Source:** `{item['path']}`  \n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"> **AI Summary:** {item['summary']}\n\n")
        f.write(f"### Text Content\n")
        f.write(f"```text\n{item['ocr_text'][:800]}...\n```\n") # Truncate for readability
        f.write(f"---\n\n")
    
    logging.info(f"Updated {safe_cat}.md")

def main():
    llm = setup_llm()
    
    processed_count = 0
    
    for source_dir in SOURCE_DIRS:
        if not os.path.exists(source_dir):
            logging.warning(f"Skipping missing directory: {source_dir}")
            continue
            
        logging.info(f"Scanning {source_dir}...")
        
        files = [f for f in os.listdir(source_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        for filename in files:
            if processed_count >= LIMIT:
                break
                
            path = os.path.join(source_dir, filename)
            
            # Simple check to avoid re-processing could be added here
            
            logging.info(f"Processing: {filename}")
            
            category, summary, ocr_text = analyze_image(llm, path)
            
            item = {
                "filename": filename,
                "path": path,
                "category": category,
                "summary": summary,
                "ocr_text": ocr_text
            }
            
            update_knowledge_base(item)
            processed_count += 1
            
        if processed_count >= LIMIT:
            logging.info("Limit reached. Stopping.")
            break
            
    logging.info("Knowledge Base Update Complete!")

if __name__ == "__main__":
    main()
