"""
Foreign vegetarian snack competitive intelligence via SerpApi.
No country restriction. Vegetarian filter only.
Targets: Tong Garden + 15 other import-ready brands.
Covers: product catalogues, global pricing, India availability, import intelligence.
Output: ph3/serp_foreign_data.json
"""
import sys, json, time, re
from pathlib import Path
from datetime import datetime, timezone
from itertools import cycle

sys.stdout.reconfigure(encoding='utf-8')

try:
    import requests
except ImportError:
    import subprocess; subprocess.run([sys.executable,"-m","pip","install","requests","--quiet"])
    import requests

ROOT = Path(__file__).resolve().parent.parent.parent
KEYS = [k.strip() for k in (ROOT/"ph3/serp_keys.txt").read_text().splitlines() if k.strip()]
key_cycle = cycle(KEYS)

SERPAPI = "https://serpapi.com/search.json"
QUERIES_USED = [0]  # mutable counter

def serp(query, engine="google", num=20, gl=None, extra=None):
    key = next(key_cycle)
    params = {"q": query, "engine": engine, "api_key": key, "num": num}
    if gl: params["gl"] = gl
    if extra: params.update(extra)
    try:
        r = requests.get(SERPAPI, params=params, timeout=20)
        QUERIES_USED[0] += 1
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def shop(query, num=20, gl=None):
    key = next(key_cycle)
    params = {"q": query, "engine": "google_shopping", "api_key": key, "num": num}
    if gl: params["gl"] = gl
    try:
        r = requests.get(SERPAPI, params=params, timeout=20)
        QUERIES_USED[0] += 1
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# ── TARGET BRANDS ──────────────────────────────────────────────────────────────
BRANDS = {
    "Tong Garden": {
        "country": "Thailand", "hq_city": "Bangkok",
        "veg_status": "Mostly Vegetarian", "website": "tonggardengroup.com",
        "profile": "Leading Thai nut/seed snack brand. Est. 1972. Strong in SE Asia.",
        "product_types": "Nuts, Seeds, Wheat Snacks, Seaweed, Mixed Snacks",
        "hs_codes": ["2008.19", "1905.90"],  # nuts, biscuits/snacks
    },
    "Oishi": {
        "country": "Thailand", "hq_city": "Bangkok",
        "veg_status": "Mostly Vegetarian (some non-veg flavors)",
        "website": "oishigroup.com",
        "profile": "Thai snack brand. Grains, extruded snacks, onion rings. Very popular in SE Asia.",
        "product_types": "Extruded Snacks, Crackers, Onion Rings, Prawn Crackers (flag!)",
        "hs_codes": ["1905.90", "2106.90"],
    },
    "Mamee": {
        "country": "Malaysia", "hq_city": "Penang",
        "veg_status": "Partially Vegetarian",
        "website": "mamee.com",
        "profile": "Malaysian snack brand. Famous for Monster noodle snack. Large SE Asia presence.",
        "product_types": "Noodle Snacks, Crackers, Biscuits, Chips",
        "hs_codes": ["1902.30", "1905.90"],
    },
    "Jack n Jill": {
        "country": "Philippines", "hq_city": "Manila",
        "veg_status": "Partially Vegetarian",
        "website": "jacknjill.com.ph",
        "profile": "Philippines' largest snack brand (Universal Robina Corp). Piattos, Nova, Mr. Chips.",
        "product_types": "Potato Chips, Corn Snacks, Prawn Crackers, Biscuits",
        "hs_codes": ["2005.20", "1905.90"],
    },
    "Want Want": {
        "country": "Taiwan", "hq_city": "Taipei / Shanghai",
        "veg_status": "Mostly Vegetarian",
        "website": "want-want.com",
        "profile": "Taiwan/China snack giant. Rice crackers, senbei, milk candy. Huge in Asia.",
        "product_types": "Rice Crackers, Senbei, Puffed Rice, Biscuits",
        "hs_codes": ["1905.90", "1904.10"],
    },
    "Calbee": {
        "country": "Japan", "hq_city": "Tokyo",
        "veg_status": "Partially Vegetarian (some flavors)",
        "website": "calbee.com",
        "profile": "Japan's largest snack company. Jagabee, Harvest Snaps. Global premium positioning.",
        "product_types": "Potato Chips, Corn Snacks, Pea Crisps, Wheat Snacks",
        "hs_codes": ["2005.20", "1905.90"],
    },
    "Hippeas": {
        "country": "UK / USA", "hq_city": "London",
        "veg_status": "100% Vegan Certified",
        "website": "hippeas.com",
        "profile": "Organic chickpea puffs. B-Corp certified. Huge in UK/US premium health snack segment.",
        "product_types": "Chickpea Puffs, Chickpea Chips, Veggie Straws",
        "hs_codes": ["1904.20", "2106.90"],
    },
    "Harvest Snaps": {
        "country": "USA", "hq_city": "Los Angeles",
        "veg_status": "100% Vegetarian",
        "website": "harvestsnaps.com",
        "profile": "Green pea/lentil/black bean crisps. Baked, high protein, clean label. Fast-growing.",
        "product_types": "Pea Crisps, Lentil Snaps, Black Bean Chips",
        "hs_codes": ["2106.90", "2005.51"],
    },
    "Tyrrell's": {
        "country": "UK", "hq_city": "Herefordshire",
        "veg_status": "Mostly Vegetarian",
        "website": "tyrrellssnacks.co.uk",
        "profile": "UK premium hand-cooked crisp brand. Wonky vegetable crisps, kettle-cooked. Premium tier.",
        "product_types": "Hand-Cooked Crisps, Vegetable Crisps, Popcorn",
        "hs_codes": ["2005.20", "1904.10"],
    },
    "Nongshim": {
        "country": "South Korea", "hq_city": "Seoul",
        "veg_status": "Partially Vegetarian",
        "website": "nongshim.com",
        "profile": "Korea's top snack/noodle brand. Shrimp Crackers (flag for veg), Honey Butter Chips.",
        "product_types": "Shrimp Crackers, Honey Crackers, Rice Snacks, Noodles",
        "hs_codes": ["1905.90", "1902.30"],
    },
    "Lotte": {
        "country": "South Korea / Japan", "hq_city": "Seoul",
        "veg_status": "Partially Vegetarian",
        "website": "lotte.co.kr",
        "profile": "Korean/Japanese FMCG giant. Pepero, Koala March, Ghana Chocolate + many snacks.",
        "product_types": "Biscuits, Crackers, Chocolate Snacks, Chips",
        "hs_codes": ["1905.90", "1806.32"],
    },
    "Wonderful Pistachios": {
        "country": "USA", "hq_city": "California",
        "veg_status": "100% Vegetarian (natural nut)",
        "website": "wonderful.com",
        "profile": "California pistachios. No-shell, In-shell. Mass market in USA. Clean 1-ingredient.",
        "product_types": "Pistachios (in-shell, no-shell, flavored)",
        "hs_codes": ["0802.51", "2008.19"],
    },
    "Kettle Brand": {
        "country": "USA", "hq_city": "Salem, Oregon",
        "veg_status": "Mostly Vegetarian",
        "website": "kettlebrand.com",
        "profile": "Premium kettle-cooked potato chips. Natural ingredients, non-GMO. Health-aware positioning.",
        "product_types": "Kettle Chips, Baked Chips, Krinkle Cut",
        "hs_codes": ["2005.20"],
    },
    "Indomie": {
        "country": "Indonesia", "hq_city": "Jakarta",
        "veg_status": "Partially Vegetarian (some flavors vegetarian)",
        "website": "indomie.com",
        "profile": "World's best-selling instant noodle. Goreng (dry-fry) version popular as snack.",
        "product_types": "Instant Noodles, Noodle Snacks",
        "hs_codes": ["1902.30"],
    },
    "Pocky / Glico": {
        "country": "Japan", "hq_city": "Osaka",
        "veg_status": "Mostly Vegetarian",
        "website": "glico.com",
        "profile": "Glico's Pocky stick biscuits. Already in Indian import market. Multiple flavors.",
        "product_types": "Stick Biscuits, Pretz, Collon",
        "hs_codes": ["1905.90"],
    },
}

# ── QUERY SETS ─────────────────────────────────────────────────────────────────
# Each query = 1 API credit. We have 5 keys × 2500 = 12,500 total.

SHOPPING_QUERIES = []
SEARCH_QUERIES = []

# Per-brand shopping queries (global, no country filter)
for brand_name in BRANDS:
    SHOPPING_QUERIES.append((f"shop_{brand_name.lower().replace(' ','_')}_global",
                              f"{brand_name} snacks vegetarian buy"))
    SHOPPING_QUERIES.append((f"shop_{brand_name.lower().replace(' ','_')}_india",
                              f"{brand_name} snacks India import buy online"))

# Tong Garden deep-dive shopping (extra queries since it's the anchor brand)
SHOPPING_QUERIES += [
    ("tg_nuts",      "Tong Garden nuts seeds snack buy"),
    ("tg_seaweed",   "Tong Garden seaweed snack buy"),
    ("tg_wheat",     "Tong Garden wheat baked snack buy"),
    ("tg_india",     "Tong Garden snacks India price"),
    ("tg_250g",      "Tong Garden 250g snack pack buy"),
    ("hippeas_all",  "Hippeas chickpea puffs all flavors buy"),
    ("harvest_all",  "Harvest Snaps green pea crisps all flavors buy"),
    ("oishi_veg",    "Oishi snack vegetarian buy"),
    ("mamee_veg",    "Mamee snack vegetarian crackers buy"),
    ("want_want_all","Want Want rice crackers buy"),
    ("nongshim_veg", "Nongshim honey crackers vegetarian buy"),
    ("tyrells_veg",  "Tyrrell's crisps vegetarian hand cooked buy"),
    ("kettle_veg",   "Kettle Brand chips vegetarian buy"),
    ("calbee_all",   "Calbee snacks international vegetarian buy"),
    ("foreign_veg_india", "imported vegetarian snacks India Rs 50 100 buy online"),
    ("asian_snacks_india","Asian snacks India import buy online vegetarian"),
    ("intl_snacks_india", "international snacks India Amazon BigBasket import vegetarian"),
]

# Per-brand deep search (product lists, import info, India presence)
SEARCH_QUERIES += [
    # Tong Garden comprehensive
    ("tg_full_catalogue",  "Tong Garden complete product catalogue all flavors list"),
    ("tg_india_import",    "Tong Garden snacks India import price availability Amazon"),
    ("tg_vegetarian",      "Tong Garden vegetarian products list ingredients"),
    ("tg_export",          "Tong Garden export countries distributors"),
    # Other brands full catalogues
    ("oishi_catalogue",    "Oishi snacks complete product list vegetarian Thailand"),
    ("mamee_catalogue",    "Mamee snacks complete product range vegetarian Malaysia"),
    ("jack_jill_catalogue","Jack n Jill Philippines snacks product list vegetarian"),
    ("want_want_catalogue","Want Want Taiwan rice crackers product list"),
    ("calbee_catalogue",   "Calbee snacks product range international vegetarian"),
    ("hippeas_catalogue",  "Hippeas product range all flavors vegan certified"),
    ("harvest_snaps_range","Harvest Snaps product line flavors ingredients"),
    ("nongshim_veg_list",  "Nongshim vegetarian snacks product list"),
    ("tyrells_range",      "Tyrrell's crisps full product range vegetarian"),
    ("pocky_catalogue",    "Pocky Glico product range flavors vegetarian India"),
    # Import intelligence
    ("india_import_snacks","imported snack brand India FSSAI clearance vegetarian popular"),
    ("india_import_duty",  "India import duty snacks food HS code 1905 2008 customs"),
    ("fssai_import_req",   "FSSAI import registration snacks vegetarian label requirements India"),
    ("tong_garden_dist",   "Tong Garden India distributor importer"),
    ("foreign_snacks_trend","imported foreign snacks trend India 2024 popularity"),
    ("asia_snack_india",   "Thailand Malaysia Singapore snacks India import popularity"),
    # Already in India search
    ("already_india",      "site:amazon.in imported snacks vegetarian foreign brand"),
    ("bigbasket_import",   "site:bigbasket.com international snacks imported vegetarian"),
    ("premium_snack_india","premium imported snacks India Rs 100 200 vegetarian available"),
    # Pricing intelligence
    ("tg_price_analysis",  "Tong Garden snack retail price analysis Singapore Thailand"),
    ("asia_snack_price",   "Asian snacks retail price India import margin"),
    # Health/trend angle
    ("chickpea_snack_intl","chickpea snack international brand vegan vegetarian"),
    ("pea_crisp_intl",     "pea lentil crisps international brand vegetarian import India"),
    ("nut_snack_intl",     "imported nut snack brand vegetarian India premium"),
    # Korean snacks
    ("korean_veg_snacks",  "Korean snacks vegetarian India popular buy 2024"),
    ("korean_snack_list",  "Korean vegetarian snacks product list ingredients"),
    # Japanese snacks
    ("japanese_veg_snacks","Japanese snacks vegetarian India import buy"),
    ("japanese_rice_crackers","Japanese rice crackers senbei vegetarian brand"),
]

print(f"=== SerpApi Foreign Snack Intelligence ===")
print(f"Started: {datetime.now(timezone.utc).isoformat()}")
print(f"Keys loaded: {len(KEYS)}")
print(f"Shopping queries: {len(SHOPPING_QUERIES)} | Search queries: {len(SEARCH_QUERIES)}")
print(f"Total planned: {len(SHOPPING_QUERIES)+len(SEARCH_QUERIES)}\n")

# ── RUN SHOPPING ───────────────────────────────────────────────────────────────
def parse_price(price_str):
    if not price_str: return None
    clean = re.sub(r'[^\d.]', '', price_str.replace(',',''))
    try: return float(clean)
    except: return None

def extract_currency(price_str):
    if not price_str: return "?"
    if "₹" in price_str or "Rs" in price_str: return "INR"
    if "$" in price_str: return "USD"
    if "£" in price_str: return "GBP"
    if "€" in price_str: return "EUR"
    if "฿" in price_str: return "THB"
    if "S$" in price_str: return "SGD"
    if "A$" in price_str: return "AUD"
    if "RM" in price_str: return "MYR"
    if "¥" in price_str or "JPY" in price_str: return "JPY"
    if "₩" in price_str or "KRW" in price_str: return "KRW"
    return "?"

def detect_brand(text):
    tl = (text or "").lower()
    for b in BRANDS:
        if b.lower() in tl: return b
        # Aliases
        if b == "Hippeas" and "hippeas" in tl: return b
        if b == "Harvest Snaps" and ("harvest snap" in tl or "harvest crisp" in tl): return b
        if b == "Jack n Jill" and ("jack" in tl and "jill" in tl): return b
        if b == "Want Want" and "want-want" in tl: return b
        if b == "Pocky / Glico" and ("pocky" in tl or "pretz" in tl or "glico" in tl): return b
        if b == "Wonderful Pistachios" and "wonderful" in tl and "pistach" in tl: return b
        if b == "Kettle Brand" and "kettle" in tl and "chip" in tl: return b
        if b == "Nongshim" and ("nongshim" in tl or "honey butter" in tl): return b
    return None

def detect_veg_flag(text):
    tl = (text or "").lower()
    non_veg = ["prawn","shrimp","chicken","beef","pork","fish","meat","seafood",
                "anchovy","squid","oyster","crab","lobster","bacon"]
    veg_pos  = ["vegetarian","vegan","plant-based","no meat","no animal","chickpea",
                 "pea","lentil","rice","wheat","corn","potato","nuts","seeds"]
    has_non_veg = any(x in tl for x in non_veg)
    has_veg = any(x in tl for x in veg_pos)
    if has_non_veg: return "NON-VEG (flag)"
    if has_veg: return "Vegetarian"
    return "Unknown"

def detect_size(text):
    m = re.search(r'(\d+(?:\.\d+)?)\s*(?:g\b|gm\b|gram)', text, re.I)
    if m: return float(m.group(1))
    m = re.search(r'(\d+(?:\.\d+)?)\s*(?:oz\b)', text, re.I)
    if m: return round(float(m.group(1)) * 28.35, 1)
    m = re.search(r'(\d+(?:\.\d+)?)\s*(?:kg\b)', text, re.I)
    if m: return float(m.group(1)) * 1000
    return None

all_shopping_results = {}
all_products = []

print("--- SHOPPING ---")
for slug, query in SHOPPING_QUERIES:
    print(f"  [{slug}] {query[:60]}")
    d = shop(query, num=20)
    items = d.get("shopping_results", [])
    row = {"slug": slug, "query": query, "count": len(items), "products": []}

    for item in items:
        title  = item.get("title","")
        price  = item.get("price","")
        source = item.get("source","")
        brand  = detect_brand(title) or detect_brand(query)
        veg    = detect_veg_flag(title + " " + item.get("snippet",""))
        size_g = detect_size(title)

        p = {
            "brand": brand or "Unknown",
            "product_name": title,
            "price_str": price,
            "price_num": parse_price(price),
            "currency": extract_currency(price),
            "size_g": size_g,
            "veg_flag": veg,
            "source_platform": source,
            "rating": item.get("rating"),
            "reviews": item.get("reviews"),
            "link": item.get("link",""),
            "query_slug": slug,
            "data_type": "shopping",
        }
        row["products"].append(p)
        if brand or query.startswith("shop_") or query.startswith("tg_"):
            all_products.append(p)

    all_shopping_results[slug] = row
    print(f"    → {len(items)} results | brands: {set(p['brand'] for p in row['products'] if p['brand'] != 'Unknown')}")
    time.sleep(0.4)

# ── RUN SEARCH ─────────────────────────────────────────────────────────────────
all_search_results = {}

print("\n--- SEARCH ---")
for slug, query in SEARCH_QUERIES:
    print(f"  [{slug}] {query[:65]}")
    d = serp(query, num=10)
    organic = d.get("organic_results", [])
    knowledge = d.get("knowledge_graph", {})

    row = {
        "slug": slug, "query": query,
        "count": len(organic),
        "knowledge_graph": knowledge,
        "results": []
    }
    for item in organic[:8]:
        brand = detect_brand(item.get("title","")) or detect_brand(item.get("snippet",""))
        row["results"].append({
            "title": item.get("title",""),
            "link":  item.get("link",""),
            "snippet": item.get("snippet",""),
            "brand_detected": brand,
            "veg_flag": detect_veg_flag(item.get("snippet","")),
        })
    all_search_results[slug] = row
    print(f"    → {len(organic)} organic | KG: {'yes' if knowledge else 'no'}")
    time.sleep(0.4)

# ── DEDUPLICATE & ENRICH PRODUCTS ──────────────────────────────────────────────
seen = set()
products_clean = []
for p in all_products:
    k = f"{p['brand']}||{p['product_name'].lower().strip()}"
    if k not in seen and len(p['product_name']) > 4:
        seen.add(k)
        products_clean.append(p)

# Brand-level aggregation
from collections import defaultdict, Counter
brand_agg = defaultdict(lambda: {
    "products": [], "currencies": Counter(), "platforms": set(),
    "price_inr": [], "price_usd": [], "price_other": [],
})
for p in products_clean:
    b = p["brand"]
    brand_agg[b]["products"].append(p["product_name"])
    brand_agg[b]["currencies"][p["currency"]] += 1
    if p["source_platform"]: brand_agg[b]["platforms"].add(p["source_platform"])
    if p["price_num"]:
        if p["currency"] == "INR": brand_agg[b]["price_inr"].append(p["price_num"])
        elif p["currency"] == "USD": brand_agg[b]["price_usd"].append(p["price_num"])
        else: brand_agg[b]["price_other"].append(p["price_num"])

brand_summary = {}
for b, v in brand_agg.items():
    brand_summary[b] = {
        "products_found": len(v["products"]),
        "sample_products": list(set(v["products"]))[:12],
        "top_currencies": dict(v["currencies"].most_common(3)),
        "platforms": sorted(v["platforms"])[:10],
        "price_inr_range": [min(v["price_inr"]), max(v["price_inr"])] if v["price_inr"] else None,
        "price_usd_range": [min(v["price_usd"]), max(v["price_usd"])] if v["price_usd"] else None,
    }

# Extract useful snippets from search for import intelligence
import_snippets = []
for slug in ["india_import_duty","fssai_import_req","tong_garden_dist","foreign_snacks_trend",
             "already_india","bigbasket_import","premium_snack_india","asia_snack_india"]:
    r = all_search_results.get(slug, {})
    for res in r.get("results",[]):
        if res.get("snippet"):
            import_snippets.append({
                "topic": slug,
                "title": res["title"],
                "snippet": res["snippet"],
                "link": res["link"],
            })

output = {
    "scraped_at": datetime.now(timezone.utc).isoformat(),
    "method": "serpapi_google_shopping_and_search",
    "queries_used": QUERIES_USED[0],
    "unique_products_found": len(products_clean),
    "brands_catalogued": list(BRANDS.keys()),
    "brands_found_in_results": list(brand_summary.keys()),
    "brand_summary": brand_summary,
    "all_products": products_clean,
    "import_intelligence_snippets": import_snippets,
    "shopping_results": {k: {"count": v["count"], "products": v["products"]}
                         for k, v in all_shopping_results.items()},
    "search_results": {k: {"count": v["count"], "results": v["results"]}
                       for k, v in all_search_results.items()},
    "brand_profiles": {b: dict(BRANDS[b], **{"summary": brand_summary.get(b, {})})
                       for b in BRANDS},
}

out = ROOT / "ph3/serp_foreign_data.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"\n=== Done ===")
print(f"Queries used: {QUERIES_USED[0]}")
print(f"Unique products: {len(products_clean)}")
print(f"Brands in results: {list(brand_summary.keys())}")
print(f"Saved: {out}")
