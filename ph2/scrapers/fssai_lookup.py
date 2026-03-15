import sys
import json
import time
import requests
from datetime import datetime
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent.parent
PH1_JSON = ROOT / "ph1" / "packet_data.json"
OUTPUT_JSON = ROOT / "ph2" / "fssai_data.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://foscos.fssai.gov.in/",
}

FOSCOS_API = "https://foscos.fssai.gov.in/api/searchLicReg?licRegNo={}&pageNo=1&pageSize=10"
FSSAI_FBO_URL = "https://www.fssai.gov.in/fbo-search"


def load_packets():
    with open(PH1_JSON, encoding="utf-8") as f:
        return json.load(f)


def build_license_map(packets):
    """Group packets by fssai_license."""
    lic_map = defaultdict(lambda: {"brand": None, "products": [], "packet_nums": []})
    for p in packets:
        lic = p.get("fssai_license")
        if not lic:
            continue
        lic_map[lic]["brand"] = p.get("brand_english")
        lic_map[lic]["products"].append(p.get("product_name_english"))
        lic_map[lic]["packet_nums"].append(p.get("packet_num"))
    return dict(lic_map)


def try_foscos_api(license_no):
    url = FOSCOS_API.format(license_no)
    result = {
        "api_accessible": False,
        "company_name_verified": None,
        "address_verified": None,
        "license_type": None,
        "valid_upto": None,
        "api_error": None,
    }
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        print(f"  FOSCOS API [{license_no}]: HTTP {resp.status_code}")
        if resp.status_code == 200:
            try:
                data = resp.json()
                # API may return list or dict with licenseList / data key
                records = []
                if isinstance(data, list):
                    records = data
                elif isinstance(data, dict):
                    for key in ("licenseList", "data", "result", "items"):
                        if key in data and isinstance(data[key], list):
                            records = data[key]
                            break
                    if not records and data:
                        records = [data]

                if records:
                    rec = records[0]
                    result["api_accessible"] = True
                    result["company_name_verified"] = rec.get("businessName") or rec.get("companyName") or rec.get("fboName") or rec.get("name")
                    result["address_verified"] = rec.get("address") or rec.get("premisesAddress")
                    result["license_type"] = rec.get("licenseType") or rec.get("regType")
                    result["valid_upto"] = rec.get("validUpto") or rec.get("expiryDate") or rec.get("validTo")
                    print(f"    -> Found company: {result['company_name_verified']}")
                else:
                    result["api_error"] = "200 OK but empty data — license may not be in database or response format changed"
            except Exception as je:
                result["api_error"] = f"200 OK but JSON parse failed: {je}"
        elif resp.status_code == 403:
            result["api_error"] = "403 Forbidden — possible CAPTCHA or IP block"
        elif resp.status_code == 401:
            result["api_error"] = "401 Unauthorized — API key required"
        elif resp.status_code == 429:
            result["api_error"] = "429 Too Many Requests — rate limited"
        elif resp.status_code == 404:
            result["api_error"] = f"404 Not Found — license {license_no} not found in API"
        else:
            result["api_error"] = f"HTTP {resp.status_code}"
    except requests.exceptions.SSLError as e:
        result["api_error"] = f"SSL error: {e}"
    except requests.exceptions.ConnectionError as e:
        result["api_error"] = f"Connection error: {e}"
    except requests.exceptions.Timeout:
        result["api_error"] = "Request timed out after 15s"
    except Exception as e:
        result["api_error"] = f"Unexpected error: {e}"
    return result


def check_fssai_fbo(url):
    try:
        resp = requests.head(url, headers=HEADERS, timeout=10, allow_redirects=True)
        return resp.status_code < 500, f"HTTP {resp.status_code}"
    except Exception as e:
        return False, str(e)


def main():
    print("=== FSSAI License Lookup ===")
    packets = load_packets()
    print(f"Loaded {len(packets)} packets from ph1")

    lic_map = build_license_map(packets)
    unique_licenses = sorted(lic_map.keys())
    print(f"Unique FSSAI licenses: {len(unique_licenses)}")
    for lic in unique_licenses:
        info = lic_map[lic]
        print(f"  {lic} -> {info['brand']} | {info['products']}")

    # Check fssai.gov.in accessibility
    print(f"\nChecking FBO search page accessibility...")
    fbo_ok, fbo_status = check_fssai_fbo(FSSAI_FBO_URL)
    print(f"  {FSSAI_FBO_URL}: {fbo_status}")

    licenses_found = []
    manual_lookup_required = []
    auto_verified = 0

    for lic in unique_licenses:
        info = lic_map[lic]
        print(f"\nQuerying FOSCOS API for license: {lic}")
        api_result = try_foscos_api(lic)
        time.sleep(1)  # polite delay

        entry = {
            "fssai_license": lic,
            "ph1_brand": info["brand"],
            "ph1_products": info["products"],
            "ph1_packet_nums": info["packet_nums"],
            **api_result,
            "note": f"Manual lookup required at https://foscos.fssai.gov.in — search license {lic}"
        }

        if api_result["api_accessible"]:
            entry["note"] = f"Auto-verified via FOSCOS API"
            auto_verified += 1
        else:
            manual_lookup_required.append(lic)

        licenses_found.append(entry)

    output = {
        "scraped_at": datetime.now().isoformat(),
        "licenses_found": licenses_found,
        "unique_licenses": len(unique_licenses),
        "auto_verified": auto_verified,
        "manual_lookup_required": manual_lookup_required,
        "fbo_search_accessible": fbo_ok,
        "fbo_search_status": fbo_status,
        "manual_lookup_instructions": (
            "Visit https://foscos.fssai.gov.in > FBO Search > "
            "enter license number in the search box"
        ),
    }

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved to {OUTPUT_JSON}")
    print(f"Auto-verified: {auto_verified}/{len(unique_licenses)}")
    print(f"Manual lookup required: {manual_lookup_required}")


if __name__ == "__main__":
    main()
