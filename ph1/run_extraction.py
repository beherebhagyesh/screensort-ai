import sys, json, base64, time, re, requests
from pathlib import Path

LOG = open("extraction_log.txt", "w", encoding="utf-8")
def log(msg):
    print(msg, flush=True)
    LOG.write(msg + "\n")
    LOG.flush()

IMAGE_DIR = Path("Images-packets")
OUTPUT_JSON = Path("packet_data.json")
WINDOW_SIZE = 4
MODEL = "gemini-3.1-flash-lite-preview"

API_KEYS = [
    "AIzaSyC0gdMubzgdxGxXU9MV1O16cLiOPwrH_mY",
    "AIzaSyBvRmd-zmAXaBKaV823ntPaIJhN605PFAI",
]
key_idx = [0]

def api_url():
    return f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEYS[key_idx[0]]}"

def parse_json(text):
    text = text.strip()
    text = re.sub(r'^```[a-z]*\n?', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n?```$', '', text)
    text = text.strip()
    try:
        return json.loads(text)
    except:
        pass
    start = text.find('{')
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '{': depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i+1])
                except:
                    break
    return None

PROMPT = """You are a product research analyst. Extract ALL information from these snack/chips packet images.
The text may be in English, Hindi, or Marathi — read all languages carefully.

Return ONLY a valid JSON object (no markdown, no explanation, no extra text):

{
  "brand_english": "",
  "brand_local": "",
  "product_name_english": "",
  "product_name_local": "",
  "tagline_or_slogan": "",
  "variant_flavor": "",
  "flavor_intensity": "",
  "product_type": "",
  "product_shape": "",
  "texture_claims": "",
  "target_audience": "",
  "mrp_inr": null,
  "net_weight_g": null,
  "price_point_tier": "",
  "manufacturer_name": "",
  "manufacturer_address": "",
  "manufacturer_city": "",
  "manufacturer_state": "",
  "manufacturer_phone": "",
  "manufacturer_email": "",
  "fssai_license": "",
  "pkg_material_mfg": "",
  "ingredients_full": "",
  "allergens": "",
  "veg_nonveg": "",
  "calories_per_100g": null,
  "calories_per_serving": null,
  "serving_size_g": null,
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
  "pack_primary_color": "",
  "pack_secondary_color": "",
  "pack_accent_colors": "",
  "pack_background_style": "",
  "front_imagery": "",
  "pack_format": "",
  "design_style": "",
  "font_style": "",
  "pack_appeal_score": null,
  "shelf_visibility_score": null,
  "claims_on_pack": "",
  "usp_differentiator": "",
  "certifications": "",
  "barcode_visible": "",
  "country_of_origin": "",
  "best_before_months": null,
  "date_of_mfg": "",
  "batch_no": "",
  "competitive_notes": ""
}

IMPORTANT rules:
- Numbers only (no units/symbols) for numeric fields
- null if not visible
- For colors: use common color names (e.g. "bright yellow", "deep red", "metallic gold")
- pack_appeal_score: rate 1-10 how eye-catching the pack is
- shelf_visibility_score: rate 1-10 how visible it would be on a shelf from distance
- design_style: e.g. "vibrant/playful", "premium/metallic", "ethnic/traditional", "modern/minimal"
- claims_on_pack: list ALL claims (e.g. "No MSG, Baked not Fried, 0 Trans Fat")
- competitive_notes: anything notable a PM should know (unique positioning, copy, etc.)
- ingredients_full: copy the FULL ingredients list exactly as printed"""

def extract_packet(images, packet_num, retries=4):
    parts = []
    for i, p in enumerate(images):
        label = "FRONT" if i == 0 else f"BACK_{i}"
        parts.append({"text": f"[{label}]"})
        parts.append({"inline_data": {
            "mime_type": "image/jpeg",
            "data": base64.standard_b64encode(p.read_bytes()).decode()
        }})
    parts.append({"text": PROMPT})
    body = {"contents": [{"role": "user", "parts": parts}]}

    for attempt in range(retries):
        try:
            r = requests.post(api_url(), json=body, timeout=120)
            if r.status_code == 429:
                key_idx[0] = (key_idx[0] + 1) % len(API_KEYS)
                wait = 30 * (attempt + 1)
                log(f"  Rate limited, switching key, waiting {wait}s...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            resp_json = r.json()
            text = resp_json["candidates"][0]["content"]["parts"][0]["text"]
            data = parse_json(text)
            if data is None:
                log(f"  PARSE FAIL RAW: {text[-300:]}")
                data = {"competitive_notes": f"parse_error: {text[-100:]}"}
            data["packet_num"] = packet_num
            data["image_files"] = [p.name for p in images]
            return data
        except Exception as e:
            if attempt == retries - 1:
                raise
            log(f"  Retry {attempt+1}: {e}")
            time.sleep(10)
    raise RuntimeError("Max retries exceeded")


images = sorted(IMAGE_DIR.glob("*.jpg"))
log(f"Total images: {len(images)}")
packets = [images[i:i+WINDOW_SIZE] for i in range(0, len(images), WINDOW_SIZE)]
log(f"Grouped into {len(packets)} packets | Model: {MODEL}\n")

all_data = []
for i, pkt in enumerate(packets):
    log(f"[{i+1}/{len(packets)}] {pkt[0].name}")
    try:
        data = extract_packet(pkt, i+1)
        all_data.append(data)
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        log(f"  {data.get('brand_english','?')} | {data.get('product_name_english','?')} | {data.get('variant_flavor','?')} | Rs{data.get('mrp_inr','?')} | {data.get('net_weight_g','?')}g")
    except Exception as e:
        log(f"  ERROR: {e}")
        all_data.append({"packet_num": i+1, "error": str(e), "image_files": [p.name for p in pkt]})
    time.sleep(1)

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)
log(f"\nDone. {len(all_data)} packets -> {OUTPUT_JSON}")
LOG.close()
