"""
Open Food Facts API — pull full catalogues for all competitor brands.
Targets: Balaji, Gopal, Prataap/Yellow Diamond, Bikaji, Haldirams, Surya + Indian snack category.
Outputs: ph2/off_brands_data.json
"""
import sys, json, time
from pathlib import Path
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')

try:
    import requests
except ImportError:
    import subprocess; subprocess.run([sys.executable,"-m","pip","install","requests","--quiet"])
    import requests

ROOT = Path(__file__).resolve().parent.parent.parent
BASE = "https://world.openfoodfacts.net/api/v2/search"
FIELDS = "product_name,brands,quantity,categories_tags,countries_tags,nutriments,ingredients_text,code,labels_tags,packaging_tags,stores_tags"
HEADERS = {"User-Agent": "SnackCompetitiveResearch/1.0 (research project)"}

BRAND_QUERIES = [
    # Primary targets
    ("balaji",          "balaji"),
    ("balaji_wafers",   "balaji wafers"),
    ("gopal",           "gopal snacks"),
    ("gopal_namkeen",   "gopal"),
    ("prataap",         "prataap"),
    ("yellow_diamond",  "yellow diamond"),
    ("bikaji",          "bikaji"),
    ("haldirams",       "haldirams"),
    ("haldirams2",      "haldiram"),
    ("surya",           "surya"),
    # Other Indian snack brands
    ("anil_foods",      "anil"),
    ("parle_snacks",    "parle"),
    ("bikanervala",     "bikanervala"),
    ("sm_foods",        "sm foods"),
    ("chitale",         "chitale"),
]

# Also query by category: snacks from India
CATEGORY_QUERIES = [
    ("in_snacks",       "snacks", "in"),
    ("in_namkeen",      "namkeen", "in"),
    ("in_chips",        "chips", "in"),
    ("in_wafers",       "wafers", "in"),
    ("in_mixture",      "mixture", "in"),
    ("in_bhujia",       "bhujia", "in"),
    ("in_sev",          "sev", "in"),
    ("in_extruded",     "extruded snacks", "in"),
]


def fetch_brand(brand_name, page_num=1, page_size=50):
    params = {
        "brands": brand_name,
        "countries_tags": "en:india",
        "fields": FIELDS,
        "page": page_num,
        "page_size": page_size,
        "sort_by": "popularity_key",
    }
    try:
        r = requests.get(BASE, params=params, headers=HEADERS, timeout=20)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def fetch_category(category, country="in", page_num=1, page_size=50):
    params = {
        "categories_tags": category,
        "countries_tags": f"en:{country}",
        "fields": FIELDS,
        "page": page_num,
        "page_size": page_size,
        "sort_by": "popularity_key",
    }
    try:
        r = requests.get(BASE, params=params, headers=HEADERS, timeout=20)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def parse_product(p):
    nutr = p.get("nutriments", {})
    return {
        "product_name": p.get("product_name",""),
        "brands": p.get("brands",""),
        "quantity": p.get("quantity",""),
        "barcode": p.get("code",""),
        "categories": p.get("categories_tags",[])[:5],
        "ingredients": (p.get("ingredients_text","") or "")[:300],
        "calories_per100g": nutr.get("energy-kcal_100g"),
        "fat_per100g": nutr.get("fat_100g"),
        "carbs_per100g": nutr.get("carbohydrates_100g"),
        "sodium_per100g": nutr.get("sodium_100g"),
        "protein_per100g": nutr.get("proteins_100g"),
        "labels": p.get("labels_tags",[])[:5],
        "stores": p.get("stores_tags",[])[:5],
    }


print("=== Open Food Facts Brand Catalogues ===")
print(f"Started: {datetime.now(timezone.utc).isoformat()}\n")

brand_catalogues = {}
category_catalogues = {}
all_products_by_brand = {}

# Brand queries
print("--- BRAND QUERIES ---")
for slug, brand in BRAND_QUERIES:
    print(f"  [{slug}] brand='{brand}'")
    resp = fetch_brand(brand)
    products = resp.get("products", [])
    count = resp.get("count", len(products))
    parsed = [parse_product(p) for p in products if p.get("product_name")]
    brand_catalogues[slug] = {
        "brand_query": brand,
        "total_count": count,
        "fetched": len(parsed),
        "products": parsed,
    }
    # Index by normalized brand name
    for p in parsed:
        b = (p.get("brands","") or brand).strip()
        if b not in all_products_by_brand:
            all_products_by_brand[b] = []
        all_products_by_brand[b].append(p)

    print(f"    → {count} total, {len(parsed)} fetched")
    if count > 50:
        # Fetch page 2
        resp2 = fetch_brand(brand, page_num=2)
        p2 = [parse_product(p) for p in resp2.get("products",[]) if p.get("product_name")]
        brand_catalogues[slug]["products"].extend(p2)
        brand_catalogues[slug]["fetched"] += len(p2)
        print(f"    → page2: +{len(p2)} more")
        time.sleep(0.5)
    time.sleep(0.8)

# Category queries
print("\n--- CATEGORY QUERIES ---")
for slug, category, country in CATEGORY_QUERIES:
    print(f"  [{slug}] category='{category}' country={country}")
    resp = fetch_category(category, country)
    products = resp.get("products", [])
    count = resp.get("count", len(products))
    parsed = [parse_product(p) for p in products if p.get("product_name")]
    category_catalogues[slug] = {
        "category": category,
        "country": country,
        "total_count": count,
        "fetched": len(parsed),
        "products": parsed,
    }
    print(f"    → {count} total, {len(parsed)} fetched")
    time.sleep(0.8)

# Aggregate all products
all_products_flat = []
seen_codes = set()
for slug, data in {**brand_catalogues, **category_catalogues}.items():
    for p in data["products"]:
        code = p.get("barcode","")
        key = code if code else f"{p.get('brands','')}|{p.get('product_name','').lower().strip()}"
        if key and key not in seen_codes:
            seen_codes.add(key)
            p["_source_slug"] = slug
            all_products_flat.append(p)

# Group by brand
brand_groups = {}
for p in all_products_flat:
    b = (p.get("brands","") or "Unknown").strip()
    if b not in brand_groups:
        brand_groups[b] = []
    brand_groups[b].append(p)

# Brand stats
brand_stats = {
    b: {
        "product_count": len(prods),
        "has_nutrition": sum(1 for p in prods if p.get("calories_per100g")),
        "has_ingredients": sum(1 for p in prods if p.get("ingredients")),
        "sizes_found": list(set(p.get("quantity","") for p in prods if p.get("quantity")))[:10],
    }
    for b, prods in brand_groups.items()
}

output = {
    "scraped_at": datetime.now(timezone.utc).isoformat(),
    "total_unique_products": len(all_products_flat),
    "brands_found": len(brand_groups),
    "brand_stats": brand_stats,
    "all_products": all_products_flat,
    "brand_catalogues": brand_catalogues,
    "category_catalogues": category_catalogues,
}

out = ROOT / "ph2/off_brands_data.json"
out.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"\n=== Done ===")
print(f"Unique products: {len(all_products_flat)}")
print(f"Brands found: {len(brand_groups)}")
for b, stats in sorted(brand_stats.items(), key=lambda x: -x[1]['product_count'])[:15]:
    print(f"  {b}: {stats['product_count']} products")
print(f"Saved: {out}")
