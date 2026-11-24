"""
Diagnostic Pipeline Orchestrator
Sequentially coordinates the 4 diagnostic stages (DNS, TCP, TLS, HTTP)
and parallel IPv4 baseline verification for any discovered resource.
"""

import time
import logging
import ipaddress
from urllib.parse import urlparse
from typing import Dict, Any, Optional

from .dns_stage import DNSDiagnostic
from .tcp_stage import TCPDiagnostic
from .tls_stage import TLSDiagnostic
from .http_stage import HTTPDiagnostic
from ..telemetry.context import TelemetryCollector

logger = logging.getLogger(__name__)

class DiagnosticPipeline:
    """Orchestrates 4-stage protocol diagnosis across DNS, TCP, TLS, and HTTP."""

    def __init__(self):
        self.dns_stage = DNSDiagnostic()
        self.tcp_stage = TCPDiagnostic()
        self.tls_stage = TLSDiagnostic()
        self.http_stage = HTTPDiagnostic()

    def _verify_infrastructure_from_ipv4(
        self,
        report: Dict[str, Any],
        host: str,
        scheme: str,
        port: int,
        ipv6_addr: str,
    ) -> bool:
        """Verify published dual-stack infrastructure when the scanner has no IPv6 route."""
        try:
            address = ipaddress.IPv6Address(ipv6_addr)
        except ValueError:
            return False
        if not address.is_global:
            return False

        ns_audit = self.dns_stage.diagnose_nameservers(host)
        report["stages"]["dns"]["ns_audit"] = ns_audit
        if not ns_audit.get("rfc3901_compliant"):
            return False
        if not report["ipv4_baseline"].get("tcp_success"):
            return False

        baseline_ip = report["ipv4_baseline"].get("target_ipv4")
        if not baseline_ip:
            return False

        if scheme == "https":
            tls_res, _ = self.tls_stage.diagnose_ipv6(
                hostname=host,
                ipv6_addr=baseline_ip,
                port=port,
                return_socket=False,
            )
            tls_res["stage"] = "TLS_IPV4_BASELINE"
            report["stages"]["tls"] = tls_res
            if tls_res.get("status") != "TLS_SUCCESS":
                return False

        http_res = self.http_stage.diagnose_ipv6(
            url=report["url"],
            ipv6_addr=baseline_ip,
        )
        http_res["stage"] = "HTTP_IPV4_BASELINE"
        report["stages"]["http"] = http_res
        if http_res.get("status") == "HTTP_5XX_SERVER_ERROR":
            return False
        if not http_res.get("status", "").startswith("HTTP_"):
            return False

        report["overall_status"] = "INFRASTRUCTURE_VERIFIED"
        report["is_ipv6_ready"] = True
        report["provenance"] = "INFERRED_INFRASTRUCTURE"
        report["validation_mode"] = "IPV4_BASELINE_WITH_IPV6_DNS"
        report["failure_reason"] = "IPv6 wire probe unavailable; readiness inferred from published IPv6 infrastructure and IPv4 baseline reachability"
        return True

    def audit_resource(self, url: str) -> Dict[str, Any]:
        """
        Execute full multi-stage audit for a given resource URL.
        Returns complete stage breakdown and final classification.
        """
        t_pipeline_start = time.perf_counter()
        parsed = urlparse(url)
        scheme = parsed.scheme.lower() or "https"
        host = parsed.hostname or ""
        port = parsed.port or (443 if scheme == "https" else 80)

        report: Dict[str, Any] = {
            "url": url,
            "hostname": host,
            "scheme": scheme,
            "port": port,
            "overall_status": "UNKNOWN",
            "is_ipv6_ready": False,
            "provenance": "UNVERIFIED",
            "validation_mode": "NONE",
            "failed_at_stage": None,
            "failure_reason": None,
            "total_time_ms": 0.0,
            "stages": {
                "dns": None,
                "tcp": None,
                "tls": None,
                "http": None
            },
            "ipv4_baseline": {
                "has_a": False,
                "tcp_success": False,
                "target_ipv4": None
            }
        }

        # ---------------- STAGE 1: DNS ----------------
        dns_res = self.dns_stage.diagnose(host)
        report["stages"]["dns"] = dns_res
        report["ipv4_baseline"]["has_a"] = dns_res.get("has_a", False)
        
        # Test IPv4 baseline in background
        if dns_res.get("a_records"):
            v4_ip = dns_res["a_records"][0]
            report["ipv4_baseline"]["target_ipv4"] = v4_ip
            v4_tcp = self.tcp_stage.diagnose_ipv4(v4_ip, port)
            report["ipv4_baseline"]["tcp_success"] = v4_tcp["status"] == "TCP_SUCCESS"

        if not dns_res.get("has_aaaa"):
            if dns_res.get("has_a"):
                report["overall_status"] = "IPV4_ONLY_DEPENDENCY"
                report["failed_at_stage"] = "DNS"
                report["failure_reason"] = "Host lacks AAAA (IPv6) DNS record"
            else:
                report["overall_status"] = "GLOBAL_FAILURE"
                report["failed_at_stage"] = "DNS"
                report["failure_reason"] = dns_res.get("error_detail", "Domain does not resolve")
            
            report["total_time_ms"] = round((time.perf_counter() - t_pipeline_start) * 1000, 2)
            return report

        ipv6_addr = dns_res["aaaa_records"][0]

        # ---------------- STAGE 2: TCP Handshake ----------------
        tcp_res, active_sock = self.tcp_stage.diagnose_ipv6(
            ipv6_addr=ipv6_addr,
            port=port,
            return_socket=True
        )
        report["stages"]["tcp"] = tcp_res

        if tcp_res["status"] != "TCP_SUCCESS":
            local_interfaces = TelemetryCollector.get_local_interfaces()
            if tcp_res["status"] == "TCP_NO_ROUTE" and local_interfaces.get("ipv6") is None:
                if self._verify_infrastructure_from_ipv4(
                    report=report,
                    host=host,
                    scheme=scheme,
                    port=port,
                    ipv6_addr=ipv6_addr,
                ):
                    report["failed_at_stage"] = None
                    report["total_time_ms"] = round((time.perf_counter() - t_pipeline_start) * 1000, 2)
                    return report
                try:
                    is_global_ipv6 = ipaddress.IPv6Address(ipv6_addr).is_global
                except ValueError:
                    is_global_ipv6 = False
                if is_global_ipv6:
                    report["overall_status"] = "SCANNER_NO_IPV6_ROUTE"
                    report["failure_reason"] = "The scanner environment has no native IPv6 route and infrastructure verification did not pass"
                else:
                    report["overall_status"] = "BROKEN_IPV6_TCP"
                    report["failure_reason"] = "AAAA record is not a globally routable IPv6 address"
            else:
                report["overall_status"] = "BROKEN_IPV6_TCP"
                report["failure_reason"] = tcp_res.get("error_detail")
            report["failed_at_stage"] = "TCP"
            report["total_time_ms"] = round((time.perf_counter() - t_pipeline_start) * 1000, 2)
            return report

        # ---------------- STAGE 3: TLS Handshake (if HTTPS) ----------------
        active_ssl_sock = None
        if scheme == "https":
            tls_res, active_ssl_sock = self.tls_stage.diagnose_ipv6(
                hostname=host,
                ipv6_addr=ipv6_addr,
                port=port,
                existing_socket=active_sock,
                return_socket=True
            )
            report["stages"]["tls"] = tls_res

            if tls_res["status"] != "TLS_SUCCESS":
                report["overall_status"] = "BROKEN_IPV6_TLS"
                report["failed_at_stage"] = "TLS"
                report["failure_reason"] = tls_res.get("error_detail")
                report["total_time_ms"] = round((time.perf_counter() - t_pipeline_start) * 1000, 2)
                return report

        # ---------------- STAGE 4: HTTP Retrieval ----------------
        http_res = self.http_stage.diagnose_ipv6(
            url=url,
            ipv6_addr=ipv6_addr,
            existing_ssl_socket=active_ssl_sock,
            existing_tcp_socket=active_sock if scheme == "http" else None
        )
        report["stages"]["http"] = http_res

        if http_res["status"] == "HTTP_SUCCESS":
            report["overall_status"] = "FULL_IPV6_READY"
            report["is_ipv6_ready"] = True
            report["provenance"] = "DIRECT_IPV6_WIRE_PROBE"
            report["validation_mode"] = "NATIVE_IPV6"
        elif http_res["status"] == "HTTP_5XX_SERVER_ERROR":
            report["overall_status"] = "BROKEN_IPV6_HTTP"
            report["failed_at_stage"] = "HTTP"
            report["failure_reason"] = http_res.get("error_detail")
        else:
            # 4xx is reachable at network transport layer, though resource itself may be 404
            report["overall_status"] = "FULL_IPV6_READY"
            report["is_ipv6_ready"] = True
            report["provenance"] = "DIRECT_IPV6_WIRE_PROBE"
            report["validation_mode"] = "NATIVE_IPV6"
            if http_res.get("error_detail"):
                report["failure_reason"] = http_res["error_detail"]

        report["total_time_ms"] = round((time.perf_counter() - t_pipeline_start) * 1000, 2)
        return report
