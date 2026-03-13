import os
import sys
import time
import logging
import base64
import csv
import argparse
from datetime import datetime

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# AI Configuration
MODEL_PATH = "models/moondream2-text-model-f16.gguf"
MMPROJ_PATH = "models/moondream2-mmproj-f16.gguf"

# Global LLM instance
_llm_instance = None

def get_llm():
    """Lazy-load the Moondream2 LLM."""
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance
    if not os.path.exists(MODEL_PATH):
        logging.error(f"AI model not found at {MODEL_PATH}. Run download_model.py first.")
        sys.exit(1)
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
        logging.error("llama-cpp-python not installed. Run: pip install llama-cpp-python")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Failed to load LLM: {e}")
        sys.exit(1)

def image_to_base64_data_uri(image_path):
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode('utf-8')
    ext = os.path.splitext(image_path)[1].lower().replace('.', '')
    if ext == 'jpg':
        ext = 'jpeg'
    return f"data:image/{ext};base64,{encoded}"

def is_front_of_packet(image_path):
    """Ask AI if this is the front of a product packet."""
    llm = get_llm()
    try:
        data_uri = image_to_base64_data_uri(image_path)
        messages = [
            {"role": "system", "content": "You are a helpful assistant that analyzes images of products."},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": data_uri}},
                {"type": "text", "text": "Is this image the front of a product packaging (like a chip packet)? Answer exactly 'Yes' or 'No'."}
            ]}
        ]
        response = llm.create_chat_completion(messages=messages, max_tokens=10)
        content = response["choices"][0]["message"]["content"].strip().lower()
        return "yes" in content
    except Exception as e:
        logging.error(f"Error checking if front for {image_path}: {e}")
        return False

def extract_front_info(image_path):
    llm = get_llm()
    try:
        data_uri = image_to_base64_data_uri(image_path)
        messages = [
            {"role": "system", "content": "You are a helpful assistant that extracts information from product packaging."},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": data_uri}},
                {"type": "text", "text": "Extract the Brand, Product Name, dominant Colors, and Weight/Volume from this front packaging. Format the response as: Brand: [value] | Name: [value] | Colors: [value] | Weight: [value]"}
            ]}
        ]
        response = llm.create_chat_completion(messages=messages, max_tokens=150)
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(f"Error extracting front info for {image_path}: {e}")
        return ""

def extract_back_info(image_path):
    llm = get_llm()
    try:
        data_uri = image_to_base64_data_uri(image_path)
        messages = [
            {"role": "system", "content": "You are a helpful assistant that extracts information from product packaging."},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": data_uri}},
                {"type": "text", "text": "Extract the Ingredients and Nutritional Information from this packaging. Be concise. Format as: Ingredients: [value] | Nutrition: [value]"}
            ]}
        ]
        response = llm.create_chat_completion(messages=messages, max_tokens=250)
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(f"Error extracting back info for {image_path}: {e}")
        return ""

def parse_extracted_info(text, keys):
    parsed = {}
    parts = text.split('|')
    for part in parts:
        for key in keys:
            if part.strip().lower().startswith(key.lower() + ":"):
                parsed[key] = part.split(':', 1)[1].strip()
                break
    return parsed

def get_sorted_images(directory, limit):
    valid_exts = {'.jpg', '.jpeg', '.png'}
    images = []
    
    if not os.path.exists(directory):
        logging.error(f"Directory not found: {directory}")
        return []

    for filename in os.listdir(directory):
        if filename.startswith("."):
            continue
        ext = os.path.splitext(filename)[1].lower()
        if ext in valid_exts:
            filepath = os.path.join(directory, filename)
            mtime = os.path.getmtime(filepath)
            images.append((filepath, mtime))
            
    images.sort(key=lambda x: x[1])  # Sort chronologically (oldest first)
    if limit > 0:
        images = images[-limit:] # Take the most recent 'limit' images
        
    return images

def group_images(images, time_threshold_minutes=2):
    groups = []
    current_group = []
    last_mtime = 0

    threshold_seconds = time_threshold_minutes * 60

    for idx, (filepath, mtime) in enumerate(images):
        logging.info(f"Analyzing {os.path.basename(filepath)}...")
        
        # Check time gap fallback
        time_gap_exceeded = False
        if current_group and (mtime - last_mtime) > threshold_seconds:
            time_gap_exceeded = True
            logging.info(f"Time gap exceeded ({mtime - last_mtime:.1f}s). Starting new group.")

        is_front = False
        if not time_gap_exceeded:
            is_front = is_front_of_packet(filepath)
            if is_front:
                logging.info(f"AI detected 'Front' image. Starting new group.")

        if is_front or time_gap_exceeded or not current_group:
            if current_group:
                groups.append(current_group)
            current_group = [filepath]
        else:
            current_group.append(filepath)

        last_mtime = mtime

    if current_group:
        groups.append(current_group)

    logging.info(f"Formed {len(groups)} packet groups.")
    return groups

def process_groups(groups):
    results = []
    for idx, group in enumerate(groups):
        logging.info(f"Processing Group {idx + 1} ({len(group)} images)...")
        
        packet_data = {
            "Group ID": idx + 1,
            "Brand": "",
            "Product Name": "",
            "Colors": "",
            "Weight": "",
            "Ingredients": "",
            "Nutritional Info": "",
            "Image Count": len(group),
            "First Image": os.path.basename(group[0])
        }

        # Assume the first image in the group is the front
        front_image = group[0]
        logging.info(f"  Extracting front info from {os.path.basename(front_image)}")
        front_text = extract_front_info(front_image)
        front_parsed = parse_extracted_info(front_text, ["Brand", "Name", "Colors", "Weight"])
        
        packet_data["Brand"] = front_parsed.get("Brand", "")
        packet_data["Product Name"] = front_parsed.get("Name", "")
        packet_data["Colors"] = front_parsed.get("Colors", "")
        packet_data["Weight"] = front_parsed.get("Weight", "")

        # Process remaining images for back info
        all_ingredients = []
        all_nutrition = []
        for back_image in group[1:]:
            logging.info(f"  Extracting back info from {os.path.basename(back_image)}")
            back_text = extract_back_info(back_image)
            back_parsed = parse_extracted_info(back_text, ["Ingredients", "Nutrition"])
            
            if "Ingredients" in back_parsed and back_parsed["Ingredients"] not in all_ingredients:
                all_ingredients.append(back_parsed["Ingredients"])
            if "Nutrition" in back_parsed and back_parsed["Nutrition"] not in all_nutrition:
                all_nutrition.append(back_parsed["Nutrition"])

        packet_data["Ingredients"] = " | ".join(all_ingredients)
        packet_data["Nutritional Info"] = " | ".join(all_nutrition)
        
        results.append(packet_data)
        
    return results

def write_csv(results, output_file):
    if not results:
        logging.warning("No data to write.")
        return

    fieldnames = ["Group ID", "Brand", "Product Name", "Colors", "Weight", 
                  "Ingredients", "Nutritional Info", "Image Count", "First Image"]
    
    try:
        with open(output_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in results:
                writer.writerow(row)
        logging.info(f"Successfully saved inventory to {output_file}")
    except Exception as e:
        logging.error(f"Failed to write CSV: {e}")

def main():
    parser = argparse.ArgumentParser(description="Inventory Scanner for Product Packets (e.g., Chips)")
    parser.add_argument("--dir", type=str, default="/sdcard/Pictures/Screenshots", help="Directory containing images to scan")
    parser.add_argument("--output", type=str, default="inventory_output.csv", help="Output CSV file name")
    parser.add_argument("--limit", type=int, default=100, help="Number of recent images to process (0 for all)")
    parser.add_argument("--time-gap", type=float, default=2.0, help="Time gap threshold in minutes to start a new group")
    args = parser.parse_args()

    logging.info(f"Scanning directory: {args.dir}")
    images = get_sorted_images(args.dir, args.limit)
    
    if not images:
        logging.info("No images found. Exiting.")
        return

    logging.info(f"Found {len(images)} images to process.")

    # Lazy load LLM to ensure it works before starting long process
    get_llm()

    groups = group_images(images, time_threshold_minutes=args.time_gap)
    results = process_groups(groups)
    write_csv(results, args.output)

if __name__ == "__main__":
    main()