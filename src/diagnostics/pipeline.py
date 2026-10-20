"""
Diagnostic Pipeline Orchestrator
Sequentially coordinates the 4 diagnostic stages (DNS, TCP, TLS, HTTP)
and parallel IPv4 baseline verification for any discovered resource.
"""

import time
import logging
from urllib.parse import urlparse
from typing import Dict, Any, Optional

from .dns_stage import DNSDiagnostic
from .tcp_stage import TCPDiagnostic
from .tls_stage import TLSDiagnostic
from .http_stage import HTTPDiagnostic

logger = logging.getLogger(__name__)

class DiagnosticPipeline:
    """Orchestrates 4-stage protocol diagnosis across DNS, TCP, TLS, and HTTP."""

    def __init__(self):
        self.dns_stage = DNSDiagnostic()
        self.tcp_stage = TCPDiagnostic()
        self.tls_stage = TLSDiagnostic()
        self.http_stage = HTTPDiagnostic()

    def audit_resource(self, url: str) -> Dict[str, Any]:
        """
        Execute full multi-stage audit for a given resource URL.
        Returns complete stage breakdown and final classification.
        """
        t_pipeline_start = time.perf_counter()
        parsed = urlparse(url)
        scheme = parsed.scheme.lower() or "https"
        host = parsed.netloc.split(":")[0]
        port = parsed.port or (443 if scheme == "https" else 80)

        report: Dict[str, Any] = {
            "url": url,
            "hostname": host,
            "scheme": scheme,
            "port": port,
            "overall_status": "UNKNOWN",
            "is_ipv6_ready": False,
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
            report["overall_status"] = "BROKEN_IPV6_TCP"
            report["failed_at_stage"] = "TCP"
            report["failure_reason"] = tcp_res.get("error_detail")
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
        elif http_res["status"] == "HTTP_5XX_SERVER_ERROR":
            report["overall_status"] = "BROKEN_IPV6_HTTP"
            report["failed_at_stage"] = "HTTP"
            report["failure_reason"] = http_res.get("error_detail")
        else:
            # 4xx is reachable at network transport layer, though resource itself may be 404
            report["overall_status"] = "FULL_IPV6_READY"
            report["is_ipv6_ready"] = True
            if http_res.get("error_detail"):
                report["failure_reason"] = http_res["error_detail"]

        report["total_time_ms"] = round((time.perf_counter() - t_pipeline_start) * 1000, 2)
        return report
