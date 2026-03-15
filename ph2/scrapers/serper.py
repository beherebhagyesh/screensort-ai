import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PH1_DATA = REPO_ROOT / "ph1" / "packet_data.json"
PH2_DIR = REPO_ROOT / "ph2"
OUTPUT_FILE = PH2_DIR / "serper_data.json"
KEY_FILE = PH2_DIR / "serper_key.txt"

SERPER_ENDPOINT = "https://google.serper.dev/shopping"

BRAND_CATALOGUE_QUERIES = [
    "balaji wafers snacks india",
    "surya gruh udhyog snacks",
    "balaji namkeen 5 rupees",
]


def normalise_brand(brand: str) -> str:
    """Return a clean lowercase brand token for query building."""
    b = brand.lower().strip()
    # Collapse common variants to a canonical short form
    if b.startswith("balaji"):
        return "balaji"
    if b.startswith("surya"):
        return "surya"
    return b


def build_sku_query(packet: dict) -> str:
    brand = normalise_brand(packet.get("brand_english", ""))
    product = packet.get("product_name_english", "").lower().strip()
    flavor = (packet.get("variant_flavor") or "").lower().strip()

    parts = [brand, product]
    if flavor and flavor not in product:
        parts.append(flavor)
    return " ".join(p for p in parts if p)


def load_api_key() -> tuple[str | None, str | None]:
    """Return (api_key, source_label) or (None, None)."""
    env_key = os.environ.get("SERPER_API_KEY", "").strip()
    if env_key:
        return env_key, "env_var"
    if KEY_FILE.exists():
        key = KEY_FILE.read_text(encoding="utf-8").strip()
        if key:
            return key, "file"
    return None, None


def print_no_key_instructions():
    print()
    print("=" * 60)
    print("  SERPER API KEY NOT FOUND")
    print("=" * 60)
    print()
    print("To run Google Shopping searches, you need a free Serper.dev API key.")
    print()
    print("Steps:")
    print("  1. Go to https://serper.dev")
    print("  2. Sign up for a free account (2,500 searches/month)")
    print("  3. Copy your API key from the dashboard")
    print("  4. EITHER set the environment variable:")
    print("       Windows CMD:   set SERPER_API_KEY=your_key_here")
    print("       PowerShell:    $env:SERPER_API_KEY='your_key_here'")
    print("       bash/zsh:      export SERPER_API_KEY=your_key_here")
    print("  5. OR save the key to:")
    print(f"       {KEY_FILE}")
    print()
    print("Then re-run this script to execute the searches.")
    print()


def extract_results(shopping_items: list) -> list:
    out = []
    for item in shopping_items:
        out.append({
            "title": item.get("title"),
            "price": item.get("price"),
            "source": item.get("source"),
            "link": item.get("link"),
            "rating": item.get("rating"),
            "ratingCount": item.get("ratingCount"),
            "imageUrl": item.get("imageUrl"),
        })
    return out


def run_query(api_key: str, query: str) -> list:
    import requests  # local import — only needed when key is present

    try:
        resp = requests.post(
            SERPER_ENDPOINT,
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query, "gl": "in", "hl": "en", "num": 10},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("shopping", [])
    except Exception as exc:
        print(f"  [WARN] Query failed: {query!r} — {exc}")
        return []


def main():
    # Load packet data
    with open(PH1_DATA, encoding="utf-8") as f:
        packets = json.load(f)

    # Build per-SKU query list
    sku_queries = []
    for pkt in packets:
        sku_queries.append({
            "ph1_packet_num": pkt["packet_num"],
            "ph1_product": pkt.get("product_name_english", ""),
            "brand": normalise_brand(pkt.get("brand_english", "")),
            "query": build_sku_query(pkt),
        })

    all_queries = [sq["query"] for sq in sku_queries] + BRAND_CATALOGUE_QUERIES
    total_queries = len(all_queries)

    api_key, key_source = load_api_key()

    # ------------------------------------------------------------------ #
    #  No key path                                                         #
    # ------------------------------------------------------------------ #
    if not api_key:
        print_no_key_instructions()

        output = {
            "status": "awaiting_api_key",
            "instructions": (
                "1. Go to https://serper.dev  "
                "2. Sign up free (2500 searches/month)  "
                "3. Copy API key  "
                "4. Save to ph2/serper_key.txt OR set env var SERPER_API_KEY"
            ),
            "queries_prepared": all_queries,
        }
        PH2_DIR.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"Saved placeholder to: {OUTPUT_FILE}")
        print(f"Queries prepared: {total_queries}")
        sys.exit(0)

    # ------------------------------------------------------------------ #
    #  Key found — run all queries                                         #
    # ------------------------------------------------------------------ #
    print(f"API key found via: {key_source}")
    print(f"Running {total_queries} queries against Google Shopping (India)...")
    print()

    scraped_at = datetime.now(timezone.utc).isoformat()

    # SKU queries
    sku_results = []
    for i, sq in enumerate(sku_queries, 1):
        query = sq["query"]
        print(f"  [{i}/{len(sku_queries)}] {query}")
        items = run_query(api_key, query)
        results = extract_results(items)
        online_presence = len(results) > 0

        sku_results.append({
            "ph1_packet_num": sq["ph1_packet_num"],
            "ph1_product": sq["ph1_product"],
            "query": query,
            "results_count": len(results),
            "online_presence": online_presence,
            "results": results,
        })
        time.sleep(1)

    # Brand catalogue queries
    catalogue_results = []
    for i, query in enumerate(BRAND_CATALOGUE_QUERIES, 1):
        print(f"  [catalogue {i}/{len(BRAND_CATALOGUE_QUERIES)}] {query}")
        items = run_query(api_key, query)
        results = extract_results(items)
        catalogue_results.append({
            "query": query,
            "results_count": len(results),
            "results": results,
        })
        time.sleep(1)

    # Summary
    skus_with_presence = sum(1 for r in sku_results if r["online_presence"])
    skus_without = len(sku_results) - skus_with_presence
    surya_skus = [r for r in sku_results if r["ph1_packet_num"] in {1, 2, 3, 4}]
    surya_online = any(r["online_presence"] for r in surya_skus)
    total_found = sum(r["results_count"] for r in sku_results) + sum(
        r["results_count"] for r in catalogue_results
    )

    output = {
        "status": "complete",
        "scraped_at": scraped_at,
        "api_key_source": key_source,
        "queries_run": total_queries,
        "sku_results": sku_results,
        "catalogue_results": catalogue_results,
        "summary": {
            "skus_with_online_presence": skus_with_presence,
            "skus_not_found_online": skus_without,
            "surya_online_presence": surya_online,
            "total_results_found": total_found,
        },
    }

    PH2_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print()
    print(f"Done. Results saved to: {OUTPUT_FILE}")
    print(f"SKUs with online presence : {skus_with_presence}/{len(sku_results)}")
    print(f"Surya online presence     : {surya_online}")
    print(f"Total shopping results    : {total_found}")


if __name__ == "__main__":
    main()
