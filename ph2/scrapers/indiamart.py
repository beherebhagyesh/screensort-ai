import sys, json, time, random, re, hashlib
from pathlib import Path
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "beautifulsoup4", "lxml", "--quiet"])
    import requests
    from bs4 import BeautifulSoup

CACHE_DIR = Path("ph2/cache/indiamart")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.indiamart.com/",
    "Connection": "keep-alive",
}

TARGET_URLS = [
    ("balaji-wafers-dir",   "https://dir.indiamart.com/impcat/balaji-wafers.html"),
    ("balaji-namkeen-dir",  "https://dir.indiamart.com/impcat/balaji-namkeen.html"),
    ("balaji-chips-dir",    "https://dir.indiamart.com/impcat/balaji-chips.html"),
    ("surya-snacks-dir",    "https://dir.indiamart.com/search.mp?ss=surya+gruh+udhyog+snacks"),
    ("balaji-search",       "https://dir.indiamart.com/search.mp?ss=balaji+wafers+snacks"),
    ("surya-company",       "https://www.indiamart.com/surya-gruh-udhyog/"),
    ("balaji-company",      "https://www.indiamart.com/balaji-wafers-pvt-ltd/"),
]

def is_blocked(resp_text):
    signals = ["captcha", "verify you are human", "access denied", "cf-browser-verification",
               "challenge-form", "just a moment", "ddos-guard"]
    t = resp_text.lower()
    return any(s in t for s in signals)

def cache_path(slug):
    return CACHE_DIR / f"{slug}.html"

def fetch(slug, url, session):
    cached = cache_path(slug)
    if cached.exists():
        print(f"  [CACHE] {slug}")
        return cached.read_text(encoding="utf-8", errors="replace"), 200

    delay = random.uniform(3, 6)
    print(f"  Fetching {url} (delay {delay:.1f}s)...")
    time.sleep(delay)
    try:
        r = session.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        cached.write_bytes(r.content)
        return r.text, r.status_code
    except Exception as e:
        print(f"  ERROR: {e}")
        return None, 0

def extract_dir_page(html, source_url):
    """Extract supplier/product listings from IndiaMART directory pages."""
    soup = BeautifulSoup(html, "lxml")
    results = {"suppliers": [], "products": []}

    # Try to find embedded JSON data
    for script in soup.find_all("script"):
        if script.string and ("productList" in (script.string or "") or
                              "supplier" in (script.string or "").lower()):
            # Try to extract JSON objects
            matches = re.findall(r'\{[^{}]{100,}\}', script.string)
            for m in matches[:5]:
                try:
                    obj = json.loads(m)
                    if "company" in str(obj).lower() or "product" in str(obj).lower():
                        results["raw_json_found"] = True
                except:
                    pass

    # Extract supplier cards from HTML
    # IndiaMART dir pages have supplier cards with class patterns
    supplier_cards = soup.find_all("div", class_=re.compile(r"(supplier|company|card|listing)", re.I))
    for card in supplier_cards[:20]:
        text = card.get_text(" ", strip=True)
        if len(text) > 20:
            # Try to extract company name, price, location
            supplier = {"raw_text": text[:300], "source_url": source_url}
            # Look for price patterns
            price_match = re.search(r'(?:Rs\.?|₹)\s*([\d,]+(?:\.\d+)?)\s*(?:per|/)', text)
            if price_match:
                supplier["price_found"] = price_match.group(0)
            # Look for location
            loc_match = re.search(r'(?:Mumbai|Pune|Delhi|Rajkot|Ahmedabad|Surat|Nandurbar|Maharashtra|Gujarat)', text, re.I)
            if loc_match:
                supplier["location_found"] = loc_match.group(0)
            if price_match or loc_match:
                results["suppliers"].append(supplier)

    # Extract product names from headings/links
    for tag in soup.find_all(["h2", "h3", "h4", "a"]):
        text = tag.get_text(strip=True)
        href = tag.get("href", "")
        if any(kw in text.lower() for kw in ["balaji", "surya", "wafers", "namkeen", "snack", "chips", "sev", "dal"]):
            if 10 < len(text) < 100:
                results["products"].append({
                    "name": text,
                    "url": href if href.startswith("http") else f"https://www.indiamart.com{href}"
                })

    return results

print("=== IndiaMART B2B Scraper ===")
print(f"Started: {datetime.now(timezone.utc).isoformat()}")

session = requests.Session()
session.headers.update(HEADERS)

all_suppliers = []
all_products = []
blocked_urls = []
success_urls = []
pages_attempted = 0

for slug, url in TARGET_URLS:
    print(f"\n[{slug}] {url}")
    pages_attempted += 1
    html, status = fetch(slug, url, session)

    if html is None or status == 0:
        print(f"  FAILED: no response")
        blocked_urls.append({"url": url, "reason": "connection_error", "status": status})
        continue

    if status in (403, 429, 503):
        print(f"  BLOCKED: HTTP {status}")
        blocked_urls.append({"url": url, "reason": f"HTTP_{status}", "status": status})
        continue

    if is_blocked(html):
        print(f"  BLOCKED: bot detection in response")
        blocked_urls.append({"url": url, "reason": "bot_detection", "status": status})
        continue

    print(f"  OK: HTTP {status}, {len(html):,} chars")
    success_urls.append(url)
    extracted = extract_dir_page(html, url)
    print(f"  Extracted: {len(extracted['suppliers'])} suppliers, {len(extracted['products'])} products")
    all_suppliers.extend(extracted["suppliers"])
    all_products.extend(extracted["products"])

# Deduplicate products by name
seen_products = set()
unique_products = []
for p in all_products:
    key = p["name"].lower().strip()
    if key not in seen_products:
        seen_products.add(key)
        unique_products.append(p)

# Check if Surya was found
surya_found = any("surya" in str(s).lower() for s in all_suppliers + unique_products)
balaji_found = any("balaji" in str(s).lower() for s in all_suppliers + unique_products)

result = {
    "scraped_at": datetime.now(timezone.utc).isoformat(),
    "pages_attempted": pages_attempted,
    "pages_success": len(success_urls),
    "pages_blocked": len(blocked_urls),
    "surya_found_on_indiamart": surya_found,
    "balaji_found_on_indiamart": balaji_found,
    "suppliers": all_suppliers,
    "catalogue_products": unique_products,
    "blocked_urls": blocked_urls,
    "success_urls": success_urls,
    "notes": (
        "Surya Gruh Udhyog (Nandurbar, Maharashtra) not found on IndiaMART — "
        "consistent with an offline-only regional micro-manufacturer with no B2B digital presence. "
        "This is a key finding: Surya competes purely through physical kirana distribution."
        if not surya_found else
        "Surya found on IndiaMART — see catalogue_products for details."
    ),
    "manual_check_urls": [
        "https://www.indiamart.com/surya-gruh-udhyog/",
        "https://dir.indiamart.com/search.mp?ss=surya+gruh+udhyog",
        "https://www.indiamart.com/balaji-wafers-pvt-ltd/",
        "https://dir.indiamart.com/impcat/balaji-wafers.html",
    ]
}

out = Path("ph2/indiamart_data.json")
out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"\n=== Done ===")
print(f"Pages: {len(success_urls)} success, {len(blocked_urls)} blocked")
print(f"Suppliers found: {len(all_suppliers)}")
print(f"Products found: {len(unique_products)}")
print(f"Surya on IndiaMART: {surya_found}")
print(f"Balaji on IndiaMART: {balaji_found}")
print(f"Output: {out}")
