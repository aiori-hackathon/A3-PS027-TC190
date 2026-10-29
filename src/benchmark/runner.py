"""
Benchmark Suite Runner (PS-027)
Automates empirical audits across 30 national target websites, computes readiness & blast radius scores,
and exports comprehensive JSON & CSV datasets.
"""

import csv
import json
import time
import logging
import re
from typing import Dict, Any, List, Optional

from .targets import BENCHMARK_TARGETS
from ..crawler.browser import BrowserCrawler
from ..crawler.collector import DependencyGraphBuilder
from ..diagnostics.pipeline import DiagnosticPipeline
from ..telemetry.context import TelemetryCollector
from ..config import REPORTS_DIR, RESOURCE_CRITICALITY_WEIGHTS

logger = logging.getLogger(__name__)

class BenchmarkRunner:
    """Orchestrates empirical measurements across curated target websites."""

    def __init__(self, headless: bool = True):
        self.crawler = BrowserCrawler(headless=headless)
        self.pipeline = DiagnosticPipeline()

    def audit_site(self, target: Dict[str, Any]) -> Dict[str, Any]:
        """Audits a single target site and all its runtime dependencies."""
        site_id = target["id"]
        name = target["name"]
        url = target["url"]
        sector = target["sector"]

        logger.info(f"Auditing site [{site_id}] {name} ({url})...")
        t_site_start = time.perf_counter()

        # 1. Headless Browser Crawl
        crawl_data = self.crawler.crawl(url)
        graph_data = DependencyGraphBuilder.build_graph(crawl_data)

        # 2. Audit Apex Domain and Authoritative Nameservers (RFC 3901)
        apex_audit = self.pipeline.audit_resource(url)
        ns_audit = self.pipeline.dns_stage.diagnose_nameservers(crawl_data["apex_domain"])

        # 3. Audit all unique hosts discovered in runtime DOM
        host_audits: Dict[str, Any] = {}
        unique_hosts = graph_data["unique_hosts"]

        for host in unique_hosts:
            host_url = f"https://{host}"
            audit_res = self.pipeline.audit_resource(host_url)
            host_audits[host] = audit_res

        # 4. Map diagnostics onto every individual resource request
        resources = crawl_data.get("requests", [])
        total_resources = len(resources)
        
        ipv6_ready_resources = 0
        ipv4_only_resources = 0
        broken_ipv6_resources = 0
        global_fail_resources = 0

        stage_failures = {"DNS": 0, "TCP": 0, "TLS": 0, "HTTP": 0}

        total_weight = 0.0
        failed_weight = 0.0

        ipv4_regex = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")
        detected_ipv4_literals: List[str] = []

        detailed_resources = []
        for req in resources:
            h = req["domain"]
            res_type = req.get("resource_type") or "other"
            weight = RESOURCE_CRITICALITY_WEIGHTS.get(res_type, 0.2)
            total_weight += weight

            # Check for hardcoded IPv4 address literals (RFC 6052 breakage)
            is_literal = bool(ipv4_regex.match(h))
            if is_literal and h not in detected_ipv4_literals:
                detected_ipv4_literals.append(h)

            diag = host_audits.get(h, {})
            is_ready = diag.get("is_ipv6_ready", False)
            status = diag.get("overall_status", "UNKNOWN")
            failed_stage = diag.get("failed_at_stage")

            if is_ready:
                ipv6_ready_resources += 1
            else:
                failed_weight += weight
                if status == "IPV4_ONLY_DEPENDENCY":
                    ipv4_only_resources += 1
                    stage_failures["DNS"] += 1
                elif status.startswith("BROKEN_IPV6_"):
                    broken_ipv6_resources += 1
                    if failed_stage in stage_failures:
                        stage_failures[failed_stage] += 1
                elif status == "GLOBAL_FAILURE":
                    global_fail_resources += 1

            detailed_resources.append({
                "url": req["url"],
                "domain": h,
                "resource_type": res_type,
                "is_first_party": req["is_first_party"],
                "is_ipv6_ready": is_ready,
                "status": status,
                "failed_stage": failed_stage,
                "criticality_weight": weight
            })

        # Calculate Readiness & Blast Radius Scores (following Webres6 Methodology)
        apex_is_ready = apex_audit.get("is_ipv6_ready", False)
        if total_resources > 0:
            subresource_score = round((ipv6_ready_resources / total_resources) * 100, 2)
            # SAP Webres6 principle: If the apex root cannot resolve/connect over IPv6, the entire site is unreachable
            readiness_score = subresource_score if apex_is_ready else 0.0
            blast_radius_score = 100.0 if not apex_is_ready else (round((failed_weight / total_weight) * 100, 2) if total_weight > 0 else 0.0)
        else:
            subresource_score = 100.0 if apex_is_ready else 0.0
            readiness_score = 100.0 if apex_is_ready else 0.0
            blast_radius_score = 0.0 if apex_is_ready else 100.0

        total_site_time_ms = round((time.perf_counter() - t_site_start) * 1000, 2)

        return {
            "id": site_id,
            "name": name,
            "url": url,
            "sector": sector,
            "apex_domain": crawl_data["apex_domain"],
            "page_title": crawl_data.get("page_title"),
            "apex_audit": {
                "has_aaaa": apex_audit.get("stages", {}).get("dns", {}).get("has_aaaa", False),
                "is_ipv6_ready": apex_is_ready,
                "status": apex_audit.get("overall_status"),
                "failed_stage": apex_audit.get("failed_at_stage"),
                "ns_audit": ns_audit
            },
            "metrics": {
                "total_resources": total_resources,
                "unique_domains": len(unique_hosts),
                "first_party_domains_count": len(graph_data["first_party_domains"]),
                "third_party_domains_count": len(graph_data["third_party_domains"]),
                "ipv6_ready_count": ipv6_ready_resources,
                "ipv4_only_count": ipv4_only_resources,
                "broken_ipv6_count": broken_ipv6_resources,
                "readiness_score_percent": readiness_score,
                "subresource_readiness_percent": subresource_score,
                "blast_radius_percent": blast_radius_score,
                "stage_failures": stage_failures,
                "ns_audit": ns_audit,
                "rfc3901_compliant": ns_audit.get("rfc3901_compliant", False),
                "ipv4_literals_count": len(detected_ipv4_literals),
                "ipv4_literals": detected_ipv4_literals,
                "methodology_reference": "SAP Webres6 (Extended with DAG & 4-Stage OSI Isolation)"
            },
            "total_audit_time_ms": total_site_time_ms,
            "graph": graph_data["graph"],
            "host_diagnostics": host_audits,
            "resources": detailed_resources
        }

    def run_benchmark(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Runs batch evaluation over benchmark targets and saves JSON/CSV datasets."""
        targets_to_run = BENCHMARK_TARGETS[:limit] if limit else BENCHMARK_TARGETS
        results = []

        logger.info(f"Starting benchmark evaluation across {len(targets_to_run)} targets...")
        telemetry_context = TelemetryCollector.get_full_context()

        for idx, target in enumerate(targets_to_run, start=1):
            logger.info(f"[{idx}/{len(targets_to_run)}] Processing {target['name']}...")
            try:
                site_report = self.audit_site(target)
                results.append(site_report)
            except Exception as e:
                logger.error(f"Error auditing {target['name']}: {e}")
                results.append({
                    "id": target["id"],
                    "name": target["name"],
                    "url": target["url"],
                    "sector": target["sector"],
                    "error": str(e)
                })

        # Calculate Summary Analytics
        completed = [r for r in results if "metrics" in r]
        avg_readiness = (
            round(sum(r["metrics"]["readiness_score_percent"] for r in completed) / len(completed), 2)
            if completed else 0.0
        )
        apex_aaaa_count = sum(1 for r in completed if r["apex_audit"]["has_aaaa"])
        apex_ready_count = sum(1 for r in completed if r["apex_audit"]["is_ipv6_ready"])

        sector_breakdown: Dict[str, List[float]] = {}
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

        # Export JSON report
        json_path = REPORTS_DIR / "results_30_sites.json"
        with open(json_path, "w") as f:
            json.dump(output_payload, f, indent=2)

        # Export CSV report
        csv_path = REPORTS_DIR / "results_30_sites.csv"
        cls_fields = [
            "id", "name", "url", "sector", "apex_domain",
            "apex_has_aaaa", "apex_ipv6_ready",
            "total_resources", "unique_domains",
            "ipv6_ready_count", "ipv4_only_count", "broken_ipv6_count",
            "readiness_score_percent", "blast_radius_percent",
            "dns_failures", "tcp_failures", "tls_failures", "http_failures",
            "total_audit_time_ms"
        ]

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=cls_fields)
            writer.writeheader()
            for r in completed:
                m = r["metrics"]
                sf = m["stage_failures"]
                writer.writerow({
                    "id": r["id"],
                    "name": r["name"],
                    "url": r["url"],
                    "sector": r["sector"],
                    "apex_domain": r["apex_domain"],
                    "apex_has_aaaa": r["apex_audit"]["has_aaaa"],
                    "apex_ipv6_ready": r["apex_audit"]["is_ipv6_ready"],
                    "total_resources": m["total_resources"],
                    "unique_domains": m["unique_domains"],
                    "ipv6_ready_count": m["ipv6_ready_count"],
                    "ipv4_only_count": m["ipv4_only_count"],
                    "broken_ipv6_count": m["broken_ipv6_count"],
                    "readiness_score_percent": m["readiness_score_percent"],
                    "blast_radius_percent": m["blast_radius_percent"],
                    "dns_failures": sf.get("DNS", 0),
                    "tcp_failures": sf.get("TCP", 0),
                    "tls_failures": sf.get("TLS", 0),
                    "http_failures": sf.get("HTTP", 0),
                    "total_audit_time_ms": r.get("total_audit_time_ms", 0)
                })

        logger.info(f"Benchmark finished! Datasets saved to {json_path} and {csv_path}")
        return output_payload
