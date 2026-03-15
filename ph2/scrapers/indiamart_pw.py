import sys, json, re, time
from pathlib import Path
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

CACHE_DIR = Path("ph2/cache/indiamart_pw")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

TARGET_PAGES = [
    ("balaji-company",    "https://www.indiamart.com/balaji-wafers-pvt-ltd/"),
    ("balaji-wafers-dir", "https://dir.indiamart.com/impcat/balaji-wafers.html"),
    ("balaji-search",     "https://dir.indiamart.com/search.mp?ss=balaji+wafers+snacks"),
    ("surya-search",      "https://dir.indiamart.com/search.mp?ss=surya+gruh+udhyog"),
    ("surya-company",     "https://www.indiamart.com/surya-gruh-udhyog/"),
]

def wait_and_cache(page, slug, wait_selector=None, wait_ms=3000):
    cached = CACHE_DIR / f"{slug}.html"
    try:
        if wait_selector:
            page.wait_for_selector(wait_selector, timeout=8000)
        else:
            page.wait_for_timeout(wait_ms)
        html = page.content()
        cached.write_text(html, encoding="utf-8")
        return html
    except PWTimeout:
        html = page.content()
        cached.write_text(html, encoding="utf-8")
        return html

def extract_company_page(page, url):
    """Extract product listings from an IndiaMART company profile page."""
    result = {"products": [], "company_info": {}, "source_url": url}
    try:
        # Company name and info
        for sel in ["h1.compnyName", "h1", ".company-name"]:
            el = page.query_selector(sel)
            if el:
                result["company_info"]["name"] = el.inner_text().strip()
                break

        # Location
        for sel in [".location", ".companyLocation", "[class*='location']"]:
            el = page.query_selector(sel)
            if el:
                result["company_info"]["location"] = el.inner_text().strip()
                break

        # Products — try multiple card patterns
        product_selectors = [
            ".product-name", ".prd-name", "[class*='prodName']",
            ".product-title", "h3.product", ".cat-name", ".prd-name a",
        ]
        seen = set()
        for sel in product_selectors:
            for el in page.query_selector_all(sel):
                name = el.inner_text().strip()
                if 3 < len(name) < 120 and name.lower() not in seen:
                    seen.add(name.lower())
                    href = ""
                    try:
                        href = el.get_attribute("href") or ""
                    except:
                        pass
                    result["products"].append({"name": name, "url": href})

        # Prices — look for price patterns near products
        price_texts = page.evaluate("""() => {
            const all = document.querySelectorAll('*');
            const results = [];
            for (const el of all) {
                const t = el.innerText || '';
                if (/(?:Rs\\.?|₹)\\s*[\\d,]+/.test(t) && t.length < 200 && el.children.length < 3) {
                    results.push(t.trim());
                }
            }
            return results.slice(0, 30);
        }""")
        result["price_mentions"] = price_texts

    except Exception as e:
        result["error"] = str(e)
    return result

def extract_dir_page(page, url):
    """Extract from IndiaMART directory listing page."""
    result = {"suppliers": [], "products": [], "source_url": url}
    try:
        page.wait_for_timeout(2000)

        # Supplier cards
        card_sels = [".supplierCard", ".supplier-card", "[class*='supplier']",
                     ".impctunit", ".listingUnit", "[class*='listing']"]
        for sel in card_sels:
            cards = page.query_selector_all(sel)
            for card in cards[:15]:
                try:
                    text = card.inner_text()
                    if len(text) > 20:
                        supplier = {"raw_text": text[:400], "source_url": url}
                        price_m = re.search(r'(?:Rs\.?|₹)\s*([\d,]+(?:\.\d+)?)', text)
                        if price_m:
                            supplier["price"] = price_m.group(0)
                        loc_m = re.search(r'(?:Mumbai|Pune|Delhi|Rajkot|Ahmedabad|Surat|Vadodara|Nandurbar|Maharashtra|Gujarat|India)', text, re.I)
                        if loc_m:
                            supplier["location"] = loc_m.group(0)
                        name_el = card.query_selector("a, h3, h4, .company")
                        if name_el:
                            supplier["company"] = name_el.inner_text().strip()[:100]
                        if price_m or loc_m or "company" in supplier:
                            result["suppliers"].append(supplier)
                except:
                    pass

        # Product links
        for el in page.query_selector_all("a"):
            try:
                href = el.get_attribute("href") or ""
                text = el.inner_text().strip()
                if ("proddetail" in href or "product" in href.lower()) and 5 < len(text) < 100:
                    result["products"].append({"name": text, "url": href})
            except:
                pass

        # All text with pricing
        result["price_mentions"] = page.evaluate("""() => {
            const results = [];
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            let node;
            while (node = walker.nextNode()) {
                const t = node.textContent.trim();
                if (/(?:Rs\\.?|₹)\\s*[\\d]/.test(t) && t.length < 200) results.push(t);
            }
            return [...new Set(results)].slice(0, 30);
        }""")

    except Exception as e:
        result["error"] = str(e)
    return result

print("=== IndiaMART Playwright Scraper ===")
print(f"Started: {datetime.now(timezone.utc).isoformat()}\n")

all_data = {}
blocked = []
success = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=[
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
    ])
    ctx = browser.new_context(
        locale="en-IN",
        timezone_id="Asia/Kolkata",
        viewport={"width": 1280, "height": 800},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        extra_http_headers={
            "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
            "Referer": "https://www.google.com/",
        }
    )
    # Block images/fonts to speed up
    ctx.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf,css}", lambda r: r.abort())

    page = ctx.new_page()

    for slug, url in TARGET_PAGES:
        print(f"[{slug}] {url}")
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=20000)
            status = resp.status if resp else 0
            html = wait_and_cache(page, slug)

            # Check for bot detection
            title = page.title().lower()
            if any(x in title for x in ["captcha", "access denied", "cloudflare", "just a moment"]):
                print(f"  BLOCKED: {title}")
                blocked.append({"url": url, "reason": title})
                continue

            print(f"  HTTP {status} | title: {page.title()[:60]}")

            if "company" in slug or "surya-company" in slug:
                data = extract_company_page(page, url)
            else:
                data = extract_dir_page(page, url)

            data["status"] = status
            data["page_title"] = page.title()
            all_data[slug] = data
            success.append(url)
            print(f"  Products: {len(data.get('products',[]))} | Suppliers: {len(data.get('suppliers',[]))}")
            time.sleep(2)

        except PWTimeout:
            print(f"  TIMEOUT")
            blocked.append({"url": url, "reason": "timeout"})
        except Exception as e:
            print(f"  ERROR: {e}")
            blocked.append({"url": url, "reason": str(e)})

    browser.close()

# Flatten all products/suppliers
all_products = []
all_suppliers = []
all_prices = []
for slug, d in all_data.items():
    all_products.extend(d.get("products", []))
    all_suppliers.extend(d.get("suppliers", []))
    all_prices.extend(d.get("price_mentions", []))

# Deduplicate products
seen = set()
unique_products = []
for p in all_products:
    k = p["name"].lower().strip()
    if k not in seen and len(k) > 3:
        seen.add(k)
        unique_products.append(p)

surya_found = any("surya" in str(v).lower() for v in all_data.values())
balaji_company = all_data.get("balaji-company", {}).get("company_info", {})

output = {
    "scraped_at": datetime.now(timezone.utc).isoformat(),
    "method": "playwright_headless_chromium",
    "pages_attempted": len(TARGET_PAGES),
    "pages_success": len(success),
    "pages_blocked": len(blocked),
    "surya_found_on_indiamart": surya_found,
    "balaji_company_info": balaji_company,
    "suppliers": all_suppliers,
    "catalogue_products": unique_products,
    "price_mentions": list(set(all_prices))[:50],
    "blocked_urls": blocked,
    "success_urls": success,
    "raw_page_data": {k: {
        "page_title": v.get("page_title"),
        "products_count": len(v.get("products", [])),
        "suppliers_count": len(v.get("suppliers", [])),
        "prices_found": len(v.get("price_mentions", [])),
        "company_info": v.get("company_info", {}),
        "error": v.get("error"),
    } for k, v in all_data.items()},
    "notes": (
        "Surya Gruh Udhyog not found on IndiaMART — offline-only micro-manufacturer, no B2B digital presence."
        if not surya_found else "Surya found — see catalogue_products."
    )
}

out = Path("ph2/indiamart_data.json")
out.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"\n=== Done ===")
print(f"Pages: {len(success)} success, {len(blocked)} blocked")
print(f"Unique products: {len(unique_products)}")
print(f"Suppliers: {len(all_suppliers)}")
print(f"Price mentions: {len(set(all_prices))}")
print(f"Surya on IndiaMART: {surya_found}")
print(f"Saved: {out}")
