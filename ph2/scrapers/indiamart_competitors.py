"""
IndiaMART B2B competitor intelligence via Playwright.
Targets: Gopal Snacks, Yellow Diamond, Bikaji, Haldirams, regional suppliers,
         Rs 5-10 wholesale namkeen/snack suppliers across Gujarat/Maharashtra/MP.
Outputs: ph2/indiamart_competitors_data.json
"""
import sys, json, re, time
from pathlib import Path
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

ROOT = Path(__file__).resolve().parent.parent.parent
CACHE_DIR = ROOT / "ph2/cache/indiamart_competitors"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ── SEARCH TARGETS ────────────────────────────────────────────────────────────
# (slug, search_url, brand_hint)
SEARCHES = [
    # B2B category discovery — wholesale Rs 5-10 snacks
    ("rs5_snacks_wholesale", "https://dir.indiamart.com/search.mp?ss=rs+5+snacks+chips+namkeen+wholesale", "general"),
    ("rs10_snacks_wholesale","https://dir.indiamart.com/search.mp?ss=rs+10+snacks+chips+wholesale", "general"),
    # Competitor brands
    ("gopal_snacks",         "https://dir.indiamart.com/search.mp?ss=gopal+snacks+gujarat", "Gopal"),
    ("yellow_diamond",       "https://dir.indiamart.com/search.mp?ss=yellow+diamond+snacks", "Yellow Diamond"),
    ("prataap_snacks",       "https://dir.indiamart.com/search.mp?ss=prataap+snacks+indore", "Prataap"),
    ("haldirams_snacks",     "https://dir.indiamart.com/search.mp?ss=haldirams+namkeen+rs5", "Haldiram"),
    ("bikaji_snacks",        "https://dir.indiamart.com/search.mp?ss=bikaji+namkeen+snacks", "Bikaji"),
    ("anil_foods",           "https://dir.indiamart.com/search.mp?ss=anil+food+products+gujarat+snacks", "Anil"),
    # Regional wholesale suppliers
    ("guj_namkeen_mfr",      "https://dir.indiamart.com/search.mp?ss=namkeen+manufacturer+gujarat+wholesale", "Gujarat"),
    ("mh_namkeen_mfr",       "https://dir.indiamart.com/search.mp?ss=namkeen+manufacturer+maharashtra+wholesale", "Maharashtra"),
    ("mp_namkeen_mfr",       "https://dir.indiamart.com/search.mp?ss=namkeen+manufacturer+madhya+pradesh", "MP"),
    # Specific product categories wholesale
    ("wafers_wholesale",     "https://dir.indiamart.com/search.mp?ss=potato+chips+wafers+manufacturer+gujarat", "general"),
    ("namkeen_wholesale",    "https://dir.indiamart.com/impcat/namkeen.html", "general"),
    ("extruded_snacks",      "https://dir.indiamart.com/search.mp?ss=extruded+snacks+manufacturer+india+wholesale", "general"),
    # Surya deeper
    ("surya_deep",           "https://dir.indiamart.com/search.mp?ss=surya+gruh+udhyog+nandurbar", "Surya"),
    # Balaji B2B
    ("balaji_wholesale",     "https://dir.indiamart.com/search.mp?ss=balaji+wafers+wholesale+distributor", "Balaji"),
]

def extract_listing_page(page, brand_hint, url):
    result = {"suppliers": [], "products": [], "price_mentions": [], "source_url": url, "brand_hint": brand_hint}
    try:
        page.wait_for_timeout(2500)

        # Extract supplier cards
        card_sels = [
            ".supplierCard", ".supplier-card", "[class*='supplier']",
            ".impctunit", ".listingUnit", "[class*='listing']",
            ".product-unit", "[class*='prodUnit']", "article",
            ".card", "[class*='Card']",
        ]
        seen_companies = set()
        for sel in card_sels:
            cards = page.query_selector_all(sel)
            for card in cards[:20]:
                try:
                    text = card.inner_text()
                    if len(text) < 15: continue

                    supplier = {"raw_text": text[:500], "source_url": url, "brand_hint": brand_hint}

                    # Company name
                    for name_sel in ["a", "h3", "h4", ".company", "[class*='company']", "[class*='Company']"]:
                        el = card.query_selector(name_sel)
                        if el:
                            t = el.inner_text().strip()
                            if 3 < len(t) < 100:
                                supplier["company"] = t
                                break

                    # Price
                    price_m = re.search(r'(?:Rs\.?|₹)\s*([\d,]+(?:\.\d+)?)', text)
                    if price_m: supplier["price"] = price_m.group(0)

                    # Location — extended list
                    loc_m = re.search(
                        r'(?:Mumbai|Pune|Delhi|Rajkot|Ahmedabad|Surat|Vadodara|Nandurbar|Nashik|'
                        r'Nagpur|Indore|Bhopal|Ujjain|Jaipur|Kolkata|Chennai|Gujarat|Maharashtra|'
                        r'Madhya Pradesh|Rajasthan|India|MP|GJ|MH)',
                        text, re.I
                    )
                    if loc_m: supplier["location"] = loc_m.group(0)

                    # MOQ
                    moq_m = re.search(r'(?:Min\.?\s*Order|MOQ)[:\s]+([^\n,]{3,40})', text, re.I)
                    if moq_m: supplier["moq"] = moq_m.group(1).strip()

                    company_key = supplier.get("company","")[:50].lower()
                    if company_key and company_key in seen_companies: continue
                    if company_key: seen_companies.add(company_key)

                    if price_m or loc_m or "company" in supplier:
                        result["suppliers"].append(supplier)
                except:
                    pass

        # Product/category links
        for el in page.query_selector_all("a"):
            try:
                href = el.get_attribute("href") or ""
                text = el.inner_text().strip()
                if (("proddetail" in href or "product" in href.lower() or
                     any(k in text.lower() for k in ["snack","chip","wafer","namkeen","sev","gathiya",
                                                      "mixture","bhujia","murukku","kurkure","chiwda",
                                                      "fryums","puffs","rings"])) and 5 < len(text) < 120):
                    result["products"].append({"name": text, "url": href})
            except:
                pass
        # Deduplicate products
        seen_p = set()
        unique_p = []
        for p in result["products"]:
            k = p["name"].lower().strip()
            if k not in seen_p:
                seen_p.add(k)
                unique_p.append(p)
        result["products"] = unique_p[:50]

        # Price mentions via JS
        result["price_mentions"] = page.evaluate("""() => {
            const results = [];
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            let node;
            while (node = walker.nextNode()) {
                const t = node.textContent.trim();
                if (/(?:Rs\\.?|₹)\\s*[\\d]/.test(t) && t.length < 200) results.push(t);
            }
            return [...new Set(results)].slice(0, 40);
        }""")

    except Exception as e:
        result["error"] = str(e)
    return result


print("=== IndiaMART Competitor Intelligence (Playwright) ===")
print(f"Started: {datetime.now(timezone.utc).isoformat()}\n")
print(f"Targets: {len(SEARCHES)} pages\n")

all_results = {}
all_suppliers = []
all_products  = []
blocked = []
success = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=[
        "--disable-blink-features=AutomationControlled", "--no-sandbox",
    ])
    ctx = browser.new_context(
        locale="en-IN", timezone_id="Asia/Kolkata",
        viewport={"width": 1280, "height": 900},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        extra_http_headers={"Accept-Language":"en-IN,en;q=0.9","Referer":"https://www.google.com/"},
    )
    ctx.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf}", lambda r: r.abort())

    page = ctx.new_page()

    for slug, url, brand_hint in SEARCHES:
        print(f"[{slug}] brand={brand_hint}")
        cached = CACHE_DIR / f"{slug}.html"
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=25000)
            status = resp.status if resp else 0

            title = page.title().lower()
            if any(x in title for x in ["captcha","access denied","cloudflare","just a moment"]):
                print(f"  BLOCKED: {title}")
                blocked.append({"slug": slug, "url": url, "reason": title})
                continue

            html = page.content()
            cached.write_text(html, encoding="utf-8")

            print(f"  HTTP {status} | {page.title()[:50]}")
            data = extract_listing_page(page, brand_hint, url)
            data["http_status"] = status
            data["page_title"] = page.title()
            all_results[slug] = data
            success.append(slug)

            all_suppliers.extend(data.get("suppliers", []))
            all_products.extend(data.get("products", []))
            print(f"  Suppliers: {len(data.get('suppliers',[]))} | Products: {len(data.get('products',[]))} | Prices: {len(data.get('price_mentions',[]))}")
            time.sleep(2)

        except PWTimeout:
            print(f"  TIMEOUT")
            blocked.append({"slug": slug, "url": url, "reason": "timeout"})
        except Exception as e:
            print(f"  ERROR: {e}")
            blocked.append({"slug": slug, "url": url, "reason": str(e)})

    browser.close()

# Deduplicate suppliers and products
seen_co = set()
unique_suppliers = []
for s in all_suppliers:
    k = (s.get("company","") or s.get("raw_text","")[:30]).lower().strip()
    if k not in seen_co:
        seen_co.add(k)
        unique_suppliers.append(s)

seen_p = set()
unique_products = []
for p in all_products:
    k = p.get("name","").lower().strip()
    if k and k not in seen_p:
        seen_p.add(k)
        unique_products.append(p)

output = {
    "scraped_at": datetime.now(timezone.utc).isoformat(),
    "method": "playwright_indiamart_competitor_b2b",
    "pages_attempted": len(SEARCHES),
    "pages_success": len(success),
    "pages_blocked": len(blocked),
    "unique_suppliers": unique_suppliers,
    "unique_products": unique_products,
    "raw_page_data": {k: {
        "page_title": v.get("page_title"),
        "brand_hint": v.get("brand_hint"),
        "suppliers_count": len(v.get("suppliers",[])),
        "products_count": len(v.get("products",[])),
        "prices_count": len(v.get("price_mentions",[])),
        "suppliers": v.get("suppliers",[]),
        "products": v.get("products",[]),
        "price_mentions": v.get("price_mentions",[]),
        "error": v.get("error"),
    } for k, v in all_results.items()},
    "blocked": blocked,
    "success_slugs": success,
}

out = ROOT / "ph2/indiamart_competitors_data.json"
out.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"\n=== Done ===")
print(f"Pages: {len(success)} success, {len(blocked)} blocked")
print(f"Unique suppliers: {len(unique_suppliers)}")
print(f"Unique products: {len(unique_products)}")
print(f"Saved: {out}")
