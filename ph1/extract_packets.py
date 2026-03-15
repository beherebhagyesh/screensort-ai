"""
Chips packet inventory extractor.
Groups images in fixed windows of WINDOW_SIZE (default 4).
Pattern: 1 front + 3 backs per packet.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import json, base64, re, time
from pathlib import Path
import anthropic

IMAGE_DIR = Path("Images-packets")
OUTPUT_JSON = Path("packet_data.json")
WINDOW_SIZE = 4   # 1 front + 3 backs; change to 5 if some packets have 4 backs

client = anthropic.Anthropic()

def encode_image(path):
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")

def parse_json(text):
    text = text.strip()
    try:
        return json.loads(text)
    except:
        pass
    start = text.find('{')
    if start == -1:
        return None
    depth = 0
    for i, c in enumerate(text[start:], start):
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i+1])
                except:
                    break
    return None

def extract_packet_data(images, packet_num, retries=3):
    content = []
    for i, img_path in enumerate(images):
        label = "FRONT" if i == 0 else f"BACK_{i}"
        content.append({"type": "text", "text": f"[{label}]"})
        content.append({"type": "image", "source": {
            "type": "base64", "media_type": "image/jpeg",
            "data": encode_image(img_path)
        }})

    content.append({"type": "text", "text": """Extract all information from these snack packet images. Return ONLY valid JSON with these keys (null if not visible):

{
  "brand": "",
  "product_name": "",
  "variant_flavor": "",
  "product_type": "",
  "mrp_inr": null,
  "net_weight_g": null,
  "manufacturer_name": "",
  "manufacturer_address": "",
  "manufacturer_phone": "",
  "manufacturer_email": "",
  "fssai_license": "",
  "ingredients": "",
  "calories_per_100g": null,
  "total_fat_g": null,
  "saturated_fat_g": null,
  "trans_fat_g": null,
  "cholesterol_mg": null,
  "total_carbs_g": null,
  "dietary_fiber_g": null,
  "sugar_g": null,
  "protein_g": null,
  "sodium_mg": null,
  "iron_mg": null,
  "calcium_mg": null,
  "vitamin_a_mcg": null,
  "vitamin_c_mg": null,
  "best_before_months": null,
  "date_of_mfg": "",
  "batch_no": "",
  "pkg_material_mfg": "",
  "veg_nonveg": "",
  "certifications": "",
  "country_of_origin": "",
  "notes": ""
}

Numbers only (no units/symbols) for numeric fields."""})

    for attempt in range(retries):
        try:
            response = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=1500,
                messages=[{"role": "user", "content": content}]
            )
            data = parse_json(response.content[0].text)
            if data is None:
                data = {"notes": f"Parse error: {response.content[0].text[:200]}"}
            data["packet_num"] = packet_num
            data["image_files"] = [p.name for p in images]
            return data
        except anthropic.RateLimitError:
            wait = 60 * (attempt + 1)
            print(f"    Rate limited, waiting {wait}s...")
            time.sleep(wait)
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(10)

    raise RuntimeError("Max retries exceeded")


def main():
    images = sorted(IMAGE_DIR.glob("*.jpg"))
    print(f"Total images: {len(images)}")

    # Group into fixed windows
    packets_grouped = []
    i = 0
    while i < len(images):
        window = images[i:i + WINDOW_SIZE]
        packets_grouped.append(window)
        i += WINDOW_SIZE

    print(f"Grouped into {len(packets_grouped)} packets of ~{WINDOW_SIZE} images each")
    print("NOTE: Review groupings after — adjust WINDOW_SIZE if needed\n")

    all_data = []
    for i, packet_images in enumerate(packets_grouped):
        print(f"[{i+1}/{len(packets_grouped)}] {packet_images[0].name} ({len(packet_images)} images)...")
        try:
            data = extract_packet_data(packet_images, i + 1)
            all_data.append(data)
            print(f"  {data.get('brand','?')} | {data.get('product_name','?')} | Rs{data.get('mrp_inr','?')} | {data.get('net_weight_g','?')}g")
        except Exception as e:
            print(f"  ERROR: {e}")
            all_data.append({
                "packet_num": i + 1,
                "error": str(e),
                "image_files": [p.name for p in packet_images]
            })
        # Small delay between packets to avoid rate limiting
        time.sleep(3)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(all_data)} packets -> {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
