#!/usr/bin/env python3
"""
Generate complete 30-site national benchmark dataset.
Audits all targets in BENCHMARK_TARGETS, persisting progress after every site.
"""

import sys
import json
import csv
import time
import logging
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.benchmark.targets import BENCHMARK_TARGETS
from src.benchmark.runner import BenchmarkRunner
from src.telemetry.context import TelemetryCollector
from src.config import REPORTS_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Generate30Sites")

JSON_PATH = REPORTS_DIR / "results_30_sites.json"
CSV_PATH = REPORTS_DIR / "results_30_sites.csv"

def save_datasets(results, telemetry_context):
    completed = [r for r in results if "metrics" in r and r.get("metrics")]
    avg_readiness = (
        round(sum(r["metrics"]["readiness_score_percent"] for r in completed) / len(completed), 2)
        if completed else 0.0
    )
    apex_aaaa_count = sum(1 for r in completed if r.get("apex_audit", {}).get("has_aaaa"))
    apex_ready_count = sum(1 for r in completed if r.get("apex_audit", {}).get("is_ipv6_ready"))

    sector_breakdown = {}
    for r in completed:
        s = r["sector"]
        sector_breakdown.setdefault(s, []).append(r["metrics"]["readiness_score_percent"])

    sector_averages = {
        s: round(sum(scores) / len(scores), 2) for s, scores in sector_breakdown.items()
    }

    output_payload = {
        "metadata": {
            "benchmark_name": "AIORI 3.0 National IPv6 Readiness Benchmark",
            "team_code": "A3-PS027-TC190",
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_targets_evaluated": len(completed),
            "average_readiness_score_percent": avg_readiness,
            "apex_aaaa_presence_count": apex_aaaa_count,
            "apex_full_ready_count": apex_ready_count,
            "sector_averages": sector_averages
        },
        "client_telemetry": telemetry_context,
        "sites": results
    }

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    cls_fields = [
        "id", "name", "url", "sector", "apex_domain",
        "apex_has_aaaa", "apex_ipv6_ready",
        "total_resources", "unique_domains",
        "ipv6_ready_count", "ipv4_only_count", "broken_ipv6_count",
        "readiness_score_percent", "blast_radius_percent",
        "dns_failures", "tcp_failures", "tls_failures", "http_failures",
        "total_audit_time_ms"
    ]

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cls_fields)
        writer.writeheader()
        for r in completed:
            m = r.get("metrics", {})
            sf = m.get("stage_failures", {})
            writer.writerow({
                "id": r.get("id"),
                "name": r.get("name"),
                "url": r.get("url"),
                "sector": r.get("sector"),
                "apex_domain": r.get("apex_domain"),
                "apex_has_aaaa": r.get("apex_audit", {}).get("has_aaaa", False),
                "apex_ipv6_ready": r.get("apex_audit", {}).get("is_ipv6_ready", False),
                "total_resources": m.get("total_resources", 0),
                "unique_domains": m.get("unique_domains", 0),
                "ipv6_ready_count": m.get("ipv6_ready_count", 0),
                "ipv4_only_count": m.get("ipv4_only_count", 0),
                "broken_ipv6_count": m.get("broken_ipv6_count", 0),
                "readiness_score_percent": m.get("readiness_score_percent", 0.0),
                "blast_radius_percent": m.get("blast_radius_percent", 0.0),
                "dns_failures": sf.get("DNS", 0),
                "tcp_failures": sf.get("TCP", 0),
                "tls_failures": sf.get("TLS", 0),
                "http_failures": sf.get("HTTP", 0),
                "total_audit_time_ms": r.get("total_audit_time_ms", 0.0)
            })

def main():
    existing_sites = {}
    telemetry_context = {}

    if JSON_PATH.exists():
        try:
            with open(JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                telemetry_context = data.get("client_telemetry", {})
                for s in data.get("sites", []):
                    if s.get("id") and "metrics" in s and not s.get("error"):
                        existing_sites[s["id"]] = s
            logger.info(f"Loaded {len(existing_sites)} previously audited sites from {JSON_PATH}")
        except Exception as e:
            logger.warning(f"Could not load existing dataset: {e}")

    if not telemetry_context:
        telemetry_context = TelemetryCollector.get_full_context()

    runner = BenchmarkRunner(headless=True)
    all_results = []

    for idx, target in enumerate(BENCHMARK_TARGETS, start=1):
        target_id = target["id"]
        if target_id in existing_sites:
            logger.info(f"[{idx}/30] Reusing cached audit for {target['name']} ({target_id})")
            all_results.append(existing_sites[target_id])
            save_datasets(all_results, telemetry_context)
            continue

        logger.info(f"[{idx}/30] Auditing live: {target['name']} ({target['url']})...")
        try:
            site_report = runner.audit_site(target)
            all_results.append(site_report)
            score = site_report.get("metrics", {}).get("readiness_score_percent", 0)
            logger.info(f"[{idx}/30] Success: {target['name']} -> Score {score}%")
        except Exception as e:
            logger.error(f"[{idx}/30] Failed auditing {target['name']}: {e}")
            all_results.append({
                "id": target["id"],
                "name": target["name"],
                "url": target["url"],
                "sector": target["sector"],
                "error": str(e)
            })

        save_datasets(all_results, telemetry_context)

    logger.info("=" * 60)
    logger.info(f"Finished benchmark generation. Total sites processed: {len(all_results)}")
    logger.info(f"Saved to {JSON_PATH} and {CSV_PATH}")

if __name__ == "__main__":
    main()
