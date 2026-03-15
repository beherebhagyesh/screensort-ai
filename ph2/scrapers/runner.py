# runner.py - runs all ph2 scrapers and produces ph2/run_summary.json
import sys, json, subprocess, time
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

SCRAPERS = [
    ("Open Food Facts", "ph2/scrapers/off_api.py",    "ph2/off_data.json"),
    ("FSSAI Lookup",    "ph2/scrapers/fssai_lookup.py","ph2/fssai_data.json"),
    ("IndiaMART",       "ph2/scrapers/indiamart.py",   "ph2/indiamart_data.json"),
    ("Serper.dev",      "ph2/scrapers/serper.py",      "ph2/serper_data.json"),
]

results = []
for name, script, output in SCRAPERS:
    print(f"\n{'='*50}")
    print(f"Running: {name}")
    start = time.time()
    try:
        r = subprocess.run(["/c/Puthon313/python", script], capture_output=True, text=True, timeout=300, encoding='utf-8')
        elapsed = time.time() - start
        output_exists = Path(output).exists()
        results.append({
            "scraper": name,
            "script": script,
            "output_file": output,
            "exit_code": r.returncode,
            "elapsed_seconds": round(elapsed, 1),
            "output_created": output_exists,
            "stdout_tail": r.stdout[-500:] if r.stdout else "",
            "stderr_tail": r.stderr[-200:] if r.stderr else "",
            "status": "success" if r.returncode == 0 and output_exists else "failed"
        })
        print(f"  Status: {'OK' if r.returncode == 0 else 'FAILED'} ({elapsed:.1f}s)")
    except Exception as e:
        results.append({"scraper": name, "status": "error", "error": str(e)})
        print(f"  ERROR: {e}")

summary = {
    "run_at": datetime.now().isoformat(),
    "scrapers_run": len(results),
    "scrapers_success": sum(1 for r in results if r.get("status") == "success"),
    "results": results
}
Path("ph2/run_summary.json").write_text(json.dumps(summary, indent=2), encoding='utf-8')
print(f"\nSummary saved to ph2/run_summary.json")
print(f"Success: {summary['scrapers_success']}/{summary['scrapers_run']}")
