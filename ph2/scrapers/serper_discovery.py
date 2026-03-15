"""
Competitive landscape discovery via Serper.dev.
Goal: find ALL brands, ALL products, ALL price points in Rs 5-10 snack market
      across Gujarat, Maharashtra, MP.
Outputs: ph2/serper_discovery_data.json
"""
import sys, json, time, re
from pathlib import Path
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')

try:
    import requests
except ImportError:
    import subprocess; subprocess.run([sys.executable,"-m","pip","install","requests","--quiet"])
    import requests

ROOT = Path(__file__).resolve().parent.parent.parent
KEY_FILE = ROOT / "ph2/serper_key.txt"
API_KEY = KEY_FILE.read_text().strip() if KEY_FILE.exists() else ""
if not API_KEY:
    import os; API_KEY = os.environ.get("SERPER_API_KEY","")

SEARCH_URL   = "https://google.serper.dev/search"
SHOPPING_URL = "https://google.serper.dev/shopping"
HEADERS = {"X-API-KEY": API_KEY, "Content-Type": "application/json"}

# ── QUERY SETS ────────────────────────────────────────────────────────────────
# Shopping: price/availability per brand
SHOPPING_QUERIES = [
    # Balaji full range
    ("balaji_rs5",           "Balaji Wafers Rs 5 snacks buy India"),
    ("balaji_rs10",          "Balaji Wafers Rs 10 snacks buy India"),
    ("balaji_namkeen_all",   "Balaji namkeen sev gathiya aloo all products"),
    # Surya
    ("surya_products",       "Surya brand snacks Maharashtra buy online"),
    # Gopal Snacks (Rajkot — major Balaji rival)
    ("gopal_rs5",            "Gopal Snacks Rs 5 chips namkeen Gujarat buy"),
    ("gopal_rs10",           "Gopal Snacks Rs 10 chips wafers Gujarat buy"),
    ("gopal_catalogue",      "Gopal Snacks all products list India buy"),
    # Yellow Diamond / Prataap (Indore, MP)
    ("yellow_diamond_rs5",   "Yellow Diamond snacks Rs 5 buy India"),
    ("yellow_diamond_rs10",  "Yellow Diamond snacks Rs 10 buy India"),
    ("prataap_catalogue",    "Prataap Snacks all products India buy"),
    # Haldirams Rs 5-10
    ("haldirams_rs5",        "Haldirams namkeen Rs 5 small pack buy"),
    ("haldirams_rs10",       "Haldirams namkeen Rs 10 pack buy online"),
    # Bikaji
    ("bikaji_rs5",           "Bikaji namkeen Rs 5 packet buy"),
    ("bikaji_rs10",          "Bikaji snacks Rs 10 buy online"),
    # Category-level
    ("rs5_category",         "Rs 5 snack packet chips namkeen India buy MRP"),
    ("rs10_category",        "Rs 10 snack packet chips namkeen India buy MRP"),
    # Local Gujarat brands
    ("gujarat_snacks",       "Gujarat local namkeen brand Rs 5 10 online buy"),
    ("gujarat_wafers",       "Gujarat chips wafers brand Rs 5 10 buy"),
    # Maharashtra local
    ("mh_local_snacks",      "Maharashtra local snack brand Rs 5 10 namkeen online"),
    # MP local
    ("mp_snacks",            "Madhya Pradesh snack brand namkeen chips Rs 5 10"),
    # Anil Food Products Gujarat
    ("anil_foods",           "Anil Food Products snacks Gujarat buy online"),
    # Bikanervala
    ("bikanervala_rs5",      "Bikanervala namkeen Rs 5 10 packet buy"),
    # Chheda's
    ("chhedas",              "Chheda snacks namkeen Mumbai Maharashtra buy"),
]

# Search: brand discovery, catalogues, company info
SEARCH_QUERIES = [
    ("balaji_full_list",      "Balaji Wafers complete product list all variants flavors catalogue"),
    ("gopal_full_list",       "Gopal Snacks complete product catalogue all variants Rajkot Gujarat"),
    ("yellow_diamond_list",   "Prataap Snacks Yellow Diamond complete product range all variants Indore"),
    ("surya_full_range",      "Surya Gruh Udhyog Nandurbar Maharashtra snacks complete product list"),
    ("haldirams_small",       "Haldirams small pack Rs 5 Rs 10 namkeen chips complete list"),
    ("bikaji_full",           "Bikaji complete product list namkeen chips Rs 5 10"),
    ("rs5_brands_india",      "Rs 5 snack brands India complete list 2024 regional Gujarat Maharashtra"),
    ("regional_competitors",  "snack namkeen brand Gujarat Maharashtra MP Rs 5 10 local regional list"),
    ("indiamart_rs5_snacks",  "site:indiamart.com Rs 5 snacks chips namkeen wholesale supplier"),
    ("gopal_website",         "Gopal Snacks Rajkot Gujarat official product list website"),
    ("prataap_website",       "Prataap Snacks Limited Indore MP product portfolio website"),
    ("local_mh_snacks",       "local snack namkeen brand Nandurbar Nashik Dhule Jalgaon Maharashtra Rs 5"),
    ("guj_namkeen_brands",    "namkeen brand Rajkot Surat Ahmedabad Gujarat local Rs 5 10"),
    ("mp_local_snacks",       "local snack brand Indore Bhopal Ujjain MP namkeen chips Rs 5 10"),
    ("snack_distributor_guj", "snack namkeen distributor wholesale Gujarat Maharashtra Rs 5 10 brands"),
]

# ── HELPERS ───────────────────────────────────────────────────────────────────
def call_serper(endpoint, query, gl="in", hl="en", num=10):
    payload = {"q": query, "gl": gl, "hl": hl, "num": num}
    try:
        r = requests.post(endpoint, headers=HEADERS, json=payload, timeout=15)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def extract_size(text):
    m = re.search(r'(\d+)\s*(?:gm?|gram)', text, re.I)
    if m: return int(m.group(1))
    return None

def extract_price(text):
    m = re.search(r'[₹Rs\.]+\s*(\d+(?:\.\d+)?)', text, re.I)
    if m: return float(m.group(1))
    return None

BRAND_PATTERNS = {
    "Balaji Wafers": ["balaji wafer", "balaji wafers"],
    "Balaji": ["balaji namkeen","balaji snack","balaji gathiya","balaji sev","balaji aloo"],
    "Surya": ["surya snack","surya gruh","surya brand"],
    "Gopal": ["gopal snack","gopal namkeen","gopal chip"],
    "Yellow Diamond": ["yellow diamond"],
    "Prataap": ["prataap snack"],
    "Haldiram": ["haldiram","haldirams"],
    "Bikaji": ["bikaji"],
    "Anil": ["anil food","anil snack"],
    "Bikanervala": ["bikanervala"],
    "Chheda": ["chheda"],
}

def detect_brand(text):
    tl = text.lower()
    for brand, patterns in BRAND_PATTERNS.items():
        if any(p in tl for p in patterns):
            return brand
    return None

# ── RUN ───────────────────────────────────────────────────────────────────────
print("=== Serper Competitive Discovery ===")
print(f"Started: {datetime.now(timezone.utc).isoformat()}\n")
print(f"Shopping queries: {len(SHOPPING_QUERIES)} | Search queries: {len(SEARCH_QUERIES)}")

shopping_results = []
search_results   = []
all_products     = []
brand_presence   = {}  # brand -> {sources, prices, products}
queries_run = 0

# Shopping queries
print("\n--- SHOPPING ---")
for slug, query in SHOPPING_QUERIES:
    print(f"  [{slug}] {query[:60]}")
    data = call_serper(SHOPPING_URL, query)
    items = data.get("shopping", [])
    queries_run += 1

    row = {"slug": slug, "query": query, "count": len(items), "items": []}
    for item in items:
        title = item.get("title","")
        price = item.get("price","")
        source = item.get("source","")
        brand = detect_brand(title) or detect_brand(query)
        size_g = extract_size(title)
        price_num = extract_price(price)

        product = {
            "brand": brand,
            "product_name": title,
            "price_str": price,
            "price_num": price_num,
            "size_g": size_g,
            "source": source,
            "rating": item.get("rating"),
            "rating_count": item.get("ratingCount"),
            "query_slug": slug,
        }
        row["items"].append(product)
        all_products.append(product)

        # Update brand_presence
        if brand:
            if brand not in brand_presence:
                brand_presence[brand] = {"products": [], "sources": set(), "prices": []}
            brand_presence[brand]["products"].append(title)
            brand_presence[brand]["sources"].add(source)
            if price_num: brand_presence[brand]["prices"].append(price_num)

    shopping_results.append(row)
    print(f"    → {len(items)} results")
    time.sleep(0.5)

# Search queries
print("\n--- SEARCH ---")
for slug, query in SEARCH_QUERIES:
    print(f"  [{slug}] {query[:60]}")
    data = call_serper(SEARCH_URL, query)
    organic = data.get("organic", [])
    queries_run += 1

    row = {"slug": slug, "query": query, "organic_count": len(organic), "results": []}
    for item in organic[:6]:
        brand = detect_brand(item.get("title","")) or detect_brand(item.get("snippet",""))
        r = {
            "title": item.get("title",""),
            "link": item.get("link",""),
            "snippet": item.get("snippet",""),
            "brand_detected": brand,
        }
        row["results"].append(r)
    search_results.append(row)
    print(f"    → {len(organic)} organic results")
    time.sleep(0.5)

# Deduplicate products by name+brand
seen = set()
unique_products = []
for p in all_products:
    key = f"{p.get('brand','?')}||{p.get('product_name','').lower().strip()}"
    if key not in seen:
        seen.add(key)
        unique_products.append(p)

# Build brand summary
brand_summary = {}
for brand, v in brand_presence.items():
    brand_summary[brand] = {
        "products_found": len(set(v["products"])),
        "sources": list(v["sources"]),
        "price_range": {
            "min": min(v["prices"]) if v["prices"] else None,
            "max": max(v["prices"]) if v["prices"] else None,
        },
        "sample_products": list(set(v["products"]))[:10],
    }

output = {
    "scraped_at": datetime.now(timezone.utc).isoformat(),
    "method": "serper_shopping_and_search",
    "queries_run": queries_run,
    "unique_products_found": len(unique_products),
    "brands_detected": list(brand_summary.keys()),
    "brand_summary": brand_summary,
    "all_products": unique_products,
    "shopping_results": shopping_results,
    "search_results": search_results,
}

out = ROOT / "ph2/serper_discovery_data.json"
out.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"\n=== Done ===")
print(f"Queries run: {queries_run}")
print(f"Unique products found: {len(unique_products)}")
print(f"Brands detected: {list(brand_summary.keys())}")
print(f"Saved: {out}")
