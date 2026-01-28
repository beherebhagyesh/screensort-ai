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
SOURCE_DIR = "/sdcard/Pictures/Screenshots"
REPORT_FILE = "smart_report.md"
MODEL_PATH = "models/moondream2-text-model-f16.gguf"
MMPROJ_PATH = "models/moondream2-mmproj-f16.gguf"
LIMIT = 2  # Limit to 5 images for testing

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_llm():
    logging.info("Loading Moondream2 Model... (This may take a moment)")
    try:
        chat_handler = MoondreamChatHandler(clip_model_path=MMPROJ_PATH)
        llm = Llama(
            model_path=MODEL_PATH,
            chat_handler=chat_handler,
            n_ctx=2048,
            n_gpu_layers=0, # CPU only for stability
            verbose=False
        )
        return llm
    except Exception as e:
        logging.error(f"Failed to load LLM: {e}")
        sys.exit(1)

def analyze_image(llm, image_path):
    # 1. Visual Analysis
    logging.info(f"Analyzing visual content of {os.path.basename(image_path)}...")
    
    # Convert image to data URI or bytes?
    # llama-cpp-python chat_handler usually expects:
    # {"role": "user", "content": [{"type": "text", "text": "..."}, {"type": "image_url", "image_url": "data:image/jpeg;base64,வைக்"}]}
    # OR file path handling depends on the handler implementation.
    # MoondreamChatHandler likely handles data URIs.
    
    import base64
    
    def image_to_base64_data_uri(path):
        with open(path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            ext = os.path.splitext(path)[1].lower().replace('.', '')
            if ext == 'jpg': ext = 'jpeg'
            return f"data:image/{ext};base64,{encoded_string}"

    try:
        data_uri = image_to_base64_data_uri(image_path)
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant that categorizes and describes screenshots."},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": data_uri}},
                {"type": "text", "text": "Describe this image briefly and categorize it into one of: Finance, Chats, Shopping, Code, Social_Media, System, Events, Food, Travel. Start with 'Category: <Category>'."}
            ]}
        ]
        
        response = llm.create_chat_completion(messages=messages, max_tokens=200)
        llm_output = response["choices"][0]["message"]["content"]
        
    except Exception as e:
        logging.error(f"LLM analysis failed: {e}")
        llm_output = "Analysis Failed"

    # 2. OCR Analysis
    logging.info("Extracting text...")
    try:
        text = pytesseract.image_to_string(Image.open(image_path)).strip()
    except Exception as e:
        text = f"OCR Failed: {e}"
        
    return llm_output, text

def generate_report(results):
    logging.info(f"Generating report: {REPORT_FILE}")
    with open(REPORT_FILE, "w") as f:
        f.write(f"# Smart Screenshot Analysis Report\n")
        f.write(f"Generated on: {datetime.now()}\n\n")
        
        for item in results:
            f.write(f"## File: {item['filename']}\n")
            f.write(f"**Path:** `{item['path']}`\n\n")
            f.write(f"### Visual Analysis (Moondream2)\n")
            f.write(f"> {item['llm_analysis'].replace(chr(10), '  '+chr(10))}\n\n")
            f.write(f"### Extracted Text (OCR)\n")
            f.write(f"```text\n{item['ocr_text'][:500]}...\n```\n") # Truncate long text
            f.write(f"---\n\n")

def main():
    if not os.path.exists(SOURCE_DIR):
        logging.error(f"Source directory not found: {SOURCE_DIR}")
        return

    llm = setup_llm()
    
    files = [f for f in os.listdir(SOURCE_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    files = files[:LIMIT] # Process only first few
    
    results = []
    
    # Initialize Report File
    with open(REPORT_FILE, "w") as f:
        f.write(f"# Smart Screenshot Analysis Report\n")
        f.write(f"Generated on: {datetime.now()}\n\n")

    for filename in files:
        path = os.path.join(SOURCE_DIR, filename)
        logging.info(f"Processing: {filename}")
        
        llm_analysis, ocr_text = analyze_image(llm, path)
        
        logging.info(f"LLM Result: {llm_analysis}")
        
        # Append to report immediately
        with open(REPORT_FILE, "a") as f:
            f.write(f"## File: {filename}\n")
            f.write(f"**Path:** `{path}`\n\n")
            f.write(f"### Visual Analysis (Moondream2)\n")
            f.write(f"> {llm_analysis.replace(chr(10), '  '+chr(10))}\n\n")
            f.write(f"### Extracted Text (OCR)\n")
            f.write(f"```text\n{ocr_text[:500]}...\n```\n")
            f.write(f"---\n\n")
        
        results.append({
            "filename": filename,
            "path": path,
            "llm_analysis": llm_analysis,
            "ocr_text": ocr_text
        })
        
    logging.info("Done!")

if __name__ == "__main__":
    main()
