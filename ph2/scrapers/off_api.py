import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
import os
import time
import requests
from datetime import datetime, timezone

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PH1_FILE = os.path.join(BASE_DIR, "ph1", "packet_data.json")
PH2_DIR = os.path.join(BASE_DIR, "ph2")
CACHE_DIR = os.path.join(PH2_DIR, "cache", "off")
OUT_FILE = os.path.join(PH2_DIR, "off_data.json")
ERROR_LOG = os.path.join(CACHE_DIR, "errors.log")

os.makedirs(CACHE_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "SnackPacketResearch/1.0 (competitor analysis; contact@screensort.ai)"
}
API_BASE = "https://world.openfoodfacts.net/api/v2"


def log_error(msg):
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] {msg}\n"
    print(f"  ERROR: {msg}", flush=True)
    with open(ERROR_LOG, "a", encoding="utf-8") as f:
        f.write(line)


def save_cache(filename, data):
    path = os.path.join(CACHE_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_json(url, params=None, label=""):
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 404:
            print(f"  404 not found: {url}", flush=True)
            return None
        else:
            log_error(f"{label} HTTP {r.status_code}: {url}")
            return None
    except requests.exceptions.Timeout:
        log_error(f"{label} TIMEOUT: {url}")
        return None
    except requests.exceptions.ConnectionError as e:
        log_error(f"{label} CONNECTION ERROR: {url} — {e}")
        return None
    except Exception as e:
        log_error(f"{label} UNEXPECTED: {url} — {e}")
        return None


def extract_nutrition(nutriments):
    if not nutriments:
        return {}
    keys = [
        "energy-kcal_100g", "energy_100g",
        "proteins_100g", "fat_100g",
        "saturated-fat_100g", "carbohydrates_100g",
        "sugars_100g", "fiber_100g",
        "sodium_100g", "salt_100g",
    ]
    result = {}
    for k in keys:
        if k in nutriments:
            short = k.replace("-", "_")
            result[short] = nutriments[k]
    return result


def build_off_url(barcode):
    return f"https://world.openfoodfacts.org/product/{barcode}"


def lookup_barcode(barcode, label):
    url = f"{API_BASE}/product/{barcode}.json"
    print(f"  Barcode lookup: {barcode}", flush=True)
    data = get_json(url, label=label)
    time.sleep(1)
    if data and data.get("status") == 1:
        return data.get("product", {})
    return None


def search_by_name(brand, product_name, label):
    params = {
        "brands": brand.lower(),
        "product_name": product_name,
        "countries_tags_en": "India",
        "fields": "product_name,brands,quantity,nutriments,ingredients_text,allergens,image_url,code",
        "page_size": 5,
        "json": 1,
    }
    url = f"{API_BASE}/search"
    print(f"  Name search: {brand} / {product_name}", flush=True)
    data = get_json(url, params=params, label=label)
    time.sleep(1)
    if not data:
        return None
    products = data.get("products", [])
    save_cache(f"search_{label.replace(' ', '_')}.json", data)
    if products:
        return products[0]
    return None


def catalogue_search(brand_query, page_size=50):
    params = {
        "brands": brand_query,
        "countries_tags_en": "India",
        "fields": "product_name,brands,quantity,nutriments,ingredients_text,code,image_url",
        "page_size": page_size,
        "json": 1,
    }
    url = f"{API_BASE}/search"
    label = f"catalogue_{brand_query}"
    print(f"  Catalogue search: brands={brand_query}", flush=True)
    data = get_json(url, params=params, label=label)
    time.sleep(1)
    if not data:
        return []
    products = data.get("products", [])
    save_cache(f"catalogue_{brand_query.replace(' ', '_')}.json", data)
    return products


def product_to_sku_match(ph1_idx, packet, product, match_type):
    code = product.get("code") or product.get("_id") or ""
    return {
        "ph1_packet_num": ph1_idx,
        "ph1_product": packet["product_name_english"],
        "ph1_brand": packet["brand_english"],
        "match_found": True,
        "match_type": match_type,
        "off_product_name": product.get("product_name") or product.get("product_name_en"),
        "off_barcode": code,
        "off_quantity": product.get("quantity"),
        "off_ingredients": product.get("ingredients_text"),
        "off_nutrition": extract_nutrition(product.get("nutriments", {})),
        "off_image_url": product.get("image_url") or product.get("image_front_url"),
        "off_url": build_off_url(code) if code else None,
    }


def empty_sku_match(ph1_idx, packet):
    return {
        "ph1_packet_num": ph1_idx,
        "ph1_product": packet["product_name_english"],
        "ph1_brand": packet["brand_english"],
        "match_found": False,
        "match_type": None,
        "off_product_name": None,
        "off_barcode": None,
        "off_quantity": None,
        "off_ingredients": None,
        "off_nutrition": {},
        "off_image_url": None,
        "off_url": None,
    }


def catalogue_product_to_discovery(product):
    code = product.get("code") or product.get("_id") or ""
    return {
        "off_barcode": code,
        "off_product_name": product.get("product_name") or product.get("product_name_en"),
        "off_brand": product.get("brands"),
        "off_quantity": product.get("quantity"),
        "off_ingredients": product.get("ingredients_text"),
        "off_nutrition": extract_nutrition(product.get("nutriments", {})),
        "off_image_url": product.get("image_url") or product.get("image_front_url"),
        "off_url": build_off_url(code) if code else None,
    }


def main():
    print("=== Open Food Facts Scraper ===", flush=True)
    print(f"Started: {datetime.now(timezone.utc).isoformat()}", flush=True)

    # Load ph1 data
    with open(PH1_FILE, encoding="utf-8") as f:
        packets = json.load(f)
    print(f"\nLoaded {len(packets)} packets from ph1/packet_data.json\n", flush=True)

    sku_matches = []

    # --- Per-SKU matching ---
    print("--- SKU Matching ---", flush=True)
    for idx, packet in enumerate(packets, 1):
        brand = packet.get("brand_english", "")
        name = packet.get("product_name_english", "")
        barcode = packet.get("barcode_visible")
        print(f"\n[{idx}/{len(packets)}] {brand} — {name}", flush=True)

        matched_product = None
        match_type = None

        # Method A: barcode lookup
        if barcode and str(barcode).strip() and str(barcode).strip().lower() not in ("null", "none", ""):
            barcode_str = str(barcode).strip()
            product = lookup_barcode(barcode_str, label=f"pkt{idx}")
            if product:
                matched_product = product
                match_type = "barcode"
                save_cache(f"barcode_{barcode_str}.json", product)
                print(f"  -> MATCH by barcode: {product.get('product_name')}", flush=True)

        # Method B: name search (if no barcode match)
        if not matched_product:
            product = search_by_name(brand, name, label=f"pkt{idx}")
            if product:
                matched_product = product
                match_type = "name_search"
                print(f"  -> MATCH by name: {product.get('product_name')}", flush=True)

        if matched_product:
            sku_matches.append(product_to_sku_match(idx, packet, matched_product, match_type))
        else:
            print(f"  -> no match found", flush=True)
            sku_matches.append(empty_sku_match(idx, packet))

    # --- Catalogue discovery ---
    print("\n--- Catalogue Discovery ---", flush=True)
    raw_catalogue = []

    for brand_query in ["balaji wafers", "balaji", "surya"]:
        products = catalogue_search(brand_query, page_size=50)
        print(f"  Found {len(products)} products for '{brand_query}'", flush=True)
        raw_catalogue.extend(products)

    # Deduplicate by barcode
    seen_codes = set()
    catalogue_discoveries = []
    for p in raw_catalogue:
        code = p.get("code") or p.get("_id") or ""
        if code and code not in seen_codes:
            seen_codes.add(code)
            catalogue_discoveries.append(catalogue_product_to_discovery(p))
        elif not code:
            # include nameless entries without dedup
            catalogue_discoveries.append(catalogue_product_to_discovery(p))

    print(f"\nUnique catalogue products: {len(catalogue_discoveries)}", flush=True)

    # --- Summary ---
    matches_found = sum(1 for m in sku_matches if m["match_found"])
    surya_found = any(
        m["match_found"] and m["ph1_brand"].lower() == "surya"
        for m in sku_matches
    )

    summary = {
        "total_ph1_skus": len(packets),
        "matches_found": matches_found,
        "catalogue_discoveries": len(catalogue_discoveries),
        "surya_found": surya_found,
    }

    output = {
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "sku_matches": sku_matches,
        "catalogue_discoveries": catalogue_discoveries,
        "summary": summary,
    }

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n=== Done ===", flush=True)
    print(f"SKU matches: {matches_found}/{len(packets)}", flush=True)
    print(f"Catalogue discoveries: {len(catalogue_discoveries)}", flush=True)
    print(f"Surya found: {surya_found}", flush=True)
    print(f"Output: {OUT_FILE}", flush=True)


if __name__ == "__main__":
    main()
