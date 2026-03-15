import sys
import json
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent
PH1_JSON = ROOT / "ph1" / "packet_data.json"
PH2_DIR = ROOT / "ph2"

DATA_SOURCES = {
    "off":      PH2_DIR / "off_data.json",
    "fssai":    PH2_DIR / "fssai_data.json",
    "indiamart": PH2_DIR / "indiamart_data.json",
    "serper":   PH2_DIR / "serper_data.json",
}
OUTPUT_JSON = PH2_DIR / "merged_data.json"


def load_json_safe(path):
    """Load JSON file, return None if missing or corrupt."""
    p = Path(path)
    if not p.exists():
        print(f"  [SKIP] {p.name} — file not found")
        return None
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  [WARN] {p.name} — failed to parse: {e}")
        return None


def build_fssai_index(fssai_data):
    """Index FSSAI results by license number."""
    if not fssai_data:
        return {}
    idx = {}
    for entry in fssai_data.get("licenses_found", []):
        lic = entry.get("fssai_license")
        if lic:
            idx[lic] = entry
    return idx


def build_off_index(off_data):
    """Index OFF results by packet_num via sku_matches."""
    if not off_data:
        return {}
    idx = {}
    for sku in off_data.get("sku_results", []):
        pnum = sku.get("packet_num")
        if pnum is not None:
            idx[pnum] = sku
    # also try sku_matches key
    for sku in off_data.get("sku_matches", []):
        pnum = sku.get("packet_num")
        if pnum is not None and pnum not in idx:
            idx[pnum] = sku
    return idx


def build_serper_index(serper_data):
    """Index Serper results by packet_num."""
    if not serper_data:
        return {}
    idx = {}
    for sku in serper_data.get("sku_results", []):
        pnum = sku.get("packet_num")
        if pnum is not None:
            idx[pnum] = sku
    return idx


def build_indiamart_index(indiamart_data):
    """Index IndiaMART results by brand name (normalised lowercase)."""
    if not indiamart_data:
        return {}
    idx = {}
    for entry in indiamart_data.get("brand_results", []):
        brand = entry.get("brand", "")
        if brand:
            idx[brand.lower()] = entry
    # also try top-level keys like 'results'
    for entry in indiamart_data.get("results", []):
        brand = entry.get("brand", "")
        if brand and brand.lower() not in idx:
            idx[brand.lower()] = entry
    return idx


def collect_new_skus(off_data, indiamart_data):
    """Collect newly discovered SKUs from catalogues."""
    new_skus = []

    if off_data:
        for item in off_data.get("catalogue_discoveries", []):
            item["source"] = "open_food_facts"
            new_skus.append(item)

    if indiamart_data:
        for item in indiamart_data.get("catalogue_products", []):
            item["source"] = "indiamart"
            new_skus.append(item)

    return new_skus


def enrich_packet(packet, off_idx, fssai_idx, indiamart_idx, serper_idx):
    enriched = dict(packet)
    pnum = packet.get("packet_num")
    lic = packet.get("fssai_license")
    brand = (packet.get("brand_english") or "").lower()

    # ── Open Food Facts ──────────────────────────────────────────
    off_match = off_idx.get(pnum)
    if off_match:
        enriched["off_matched"] = True
        enriched["off_product_name"] = off_match.get("product_name") or off_match.get("off_product_name")
        enriched["off_barcode"] = off_match.get("barcode") or off_match.get("off_barcode")
        # nutrition may be nested
        nutrition = off_match.get("nutrition") or {}
        enriched["off_nutrition"] = nutrition if nutrition else None
        enriched["off_ingredients_verified"] = off_match.get("ingredients_verified") or off_match.get("ingredients_text") or None
    else:
        enriched["off_matched"] = False
        enriched["off_product_name"] = None
        enriched["off_barcode"] = None
        enriched["off_nutrition"] = None
        enriched["off_ingredients_verified"] = None

    # ── FSSAI ─────────────────────────────────────────────────────
    fssai_match = fssai_idx.get(lic) if lic else None
    if fssai_match:
        enriched["fssai_verified"] = fssai_match.get("api_accessible", False)
        enriched["fssai_company_name_verified"] = fssai_match.get("company_name_verified")
    else:
        enriched["fssai_verified"] = False
        enriched["fssai_company_name_verified"] = None

    # ── IndiaMART ─────────────────────────────────────────────────
    indiamart_match = indiamart_idx.get(brand)
    if not indiamart_match:
        # try partial match
        for key in indiamart_idx:
            if brand in key or key in brand:
                indiamart_match = indiamart_idx[key]
                break
    if indiamart_match:
        enriched["indiamart_wholesale_price"] = indiamart_match.get("wholesale_price") or indiamart_match.get("price")
        enriched["indiamart_moq"] = indiamart_match.get("moq") or indiamart_match.get("minimum_order_quantity")
        enriched["indiamart_supplier"] = indiamart_match.get("supplier") or indiamart_match.get("company_name")
    else:
        enriched["indiamart_wholesale_price"] = None
        enriched["indiamart_moq"] = None
        enriched["indiamart_supplier"] = None

    # ── Serper ────────────────────────────────────────────────────
    serper_match = serper_idx.get(pnum)
    if serper_match:
        enriched["serper_online_presence"] = True
        enriched["serper_price"] = serper_match.get("price")
        enriched["serper_source"] = serper_match.get("source") or serper_match.get("link")
        enriched["serper_rating"] = serper_match.get("rating")
        enriched["serper_reviews"] = serper_match.get("reviews") or serper_match.get("review_count")
    else:
        enriched["serper_online_presence"] = False
        enriched["serper_price"] = None
        enriched["serper_source"] = None
        enriched["serper_rating"] = None
        enriched["serper_reviews"] = None

    # ── Online presence score (0–4) ───────────────────────────────
    score = 0
    if enriched["off_matched"]:
        score += 1
    if enriched["fssai_verified"]:
        score += 1
    if enriched["indiamart_wholesale_price"] is not None:
        score += 1
    if enriched["serper_online_presence"]:
        score += 1
    enriched["online_presence_score"] = score

    return enriched


def main():
    print("=== ph2 Merge ===")

    # Load ph1 source
    with open(PH1_JSON, encoding="utf-8") as f:
        packets = json.load(f)
    print(f"Loaded {len(packets)} packets from ph1")

    # Load all ph2 sources
    off_data       = load_json_safe(DATA_SOURCES["off"])
    fssai_data     = load_json_safe(DATA_SOURCES["fssai"])
    indiamart_data = load_json_safe(DATA_SOURCES["indiamart"])
    serper_data    = load_json_safe(DATA_SOURCES["serper"])

    # Build indexes
    off_idx       = build_off_index(off_data)
    fssai_idx     = build_fssai_index(fssai_data)
    indiamart_idx = build_indiamart_index(indiamart_data)
    serper_idx    = build_serper_index(serper_data)

    print(f"Index sizes — OFF: {len(off_idx)}, FSSAI: {len(fssai_idx)}, "
          f"IndiaMART: {len(indiamart_idx)}, Serper: {len(serper_idx)}")

    # Enrich each packet
    enriched_skus = []
    for p in packets:
        ep = enrich_packet(p, off_idx, fssai_idx, indiamart_idx, serper_idx)
        enriched_skus.append(ep)
        score = ep["online_presence_score"]
        print(f"  Packet {ep['packet_num']:>2} — {ep.get('brand_english','?')} {ep.get('product_name_english','?')[:30]} "
              f"| presence={score}/4 | OFF={ep['off_matched']} | FSSAI={ep['fssai_verified']}")

    # Collect new SKUs
    new_skus = collect_new_skus(off_data, indiamart_data)
    print(f"\nNew SKUs discovered: {len(new_skus)}")

    # Compute summary stats
    avg_score = sum(e["online_presence_score"] for e in enriched_skus) / len(enriched_skus) if enriched_skus else 0
    off_matched_count = sum(1 for e in enriched_skus if e["off_matched"])
    fssai_verified_count = sum(1 for e in enriched_skus if e["fssai_verified"])

    output = {
        "merged_at": datetime.now().isoformat(),
        "ph1_skus": len(packets),
        "enriched_skus": enriched_skus,
        "new_skus_discovered": new_skus,
        "summary": {
            "off_matched": off_matched_count,
            "fssai_verified": fssai_verified_count,
            "avg_online_presence_score": round(avg_score, 2),
        },
        "data_sources": {
            "off":       str(DATA_SOURCES["off"].relative_to(ROOT)),
            "fssai":     str(DATA_SOURCES["fssai"].relative_to(ROOT)),
            "indiamart": str(DATA_SOURCES["indiamart"].relative_to(ROOT)),
            "serper":    str(DATA_SOURCES["serper"].relative_to(ROOT)),
        },
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved to {OUTPUT_JSON}")
    print(f"Enriched: {len(enriched_skus)} SKUs | New discovered: {len(new_skus)}")
    print(f"Avg online presence score: {avg_score:.2f}/4")


if __name__ == "__main__":
    main()
