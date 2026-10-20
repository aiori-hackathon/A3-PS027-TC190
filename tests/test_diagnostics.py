"""
Unit and Integration Tests for Multi-Stage Protocol Diagnostics (PS-027)
"""

import pytest
from src.diagnostics.dns_stage import DNSDiagnostic
from src.diagnostics.tcp_stage import TCPDiagnostic
from src.diagnostics.tls_stage import TLSDiagnostic
from src.diagnostics.http_stage import HTTPDiagnostic
from src.diagnostics.pipeline import DiagnosticPipeline

def test_dns_stage_aaaa_exists():
    """Verify that a known dual-stack / IPv6 site resolves AAAA records."""
    dns_diag = DNSDiagnostic()
    res = dns_diag.diagnose("one.one.one.one")
    assert res["status"] == "AAAA_EXISTS"
    assert res["has_aaaa"] is True
    assert len(res["aaaa_records"]) > 0

def test_dns_stage_no_aaaa_detection():
    """Verify that an apex domain without AAAA is detected as NO_AAAA (IPv4-only)."""
    dns_diag = DNSDiagnostic()
    # github.com currently lacks an AAAA record on its apex web frontend
    res = dns_diag.diagnose("github.com")
    assert res["has_a"] is True
    assert res["has_aaaa"] is False
    assert res["status"] == "NO_AAAA"

def test_tcp_stage_ipv6_connect():
    """Verify direct IPv6 raw socket handshake."""
    tcp_diag = TCPDiagnostic(timeout=3.0)
    # Cloudflare public DNS IPv6
    res, sock = tcp_diag.diagnose_ipv6("2606:4700:4700::1111", port=443, return_socket=True)
    assert res["status"] == "TCP_SUCCESS"
    assert res["rtt_ms"] > 0
    if sock:
        sock.close()

def test_pipeline_ipv6_ready_site():
    """Verify full end-to-end 4-stage diagnosis on an IPv6-ready target."""
    pipeline = DiagnosticPipeline()
    res = pipeline.audit_resource("https://one.one.one.one")
    assert res["overall_status"] == "FULL_IPV6_READY"
    assert res["is_ipv6_ready"] is True
    assert res["stages"]["dns"]["has_aaaa"] is True
    assert res["stages"]["tcp"]["status"] == "TCP_SUCCESS"
    assert res["stages"]["tls"]["status"] == "TLS_SUCCESS"

def test_pipeline_ipv4_only_site():
    """Verify that an IPv4-only site is flagged at the DNS stage."""
    pipeline = DiagnosticPipeline()
    res = pipeline.audit_resource("https://github.com")
    assert res["overall_status"] == "IPV4_ONLY_DEPENDENCY"
    assert res["is_ipv6_ready"] is False
    assert res["failed_at_stage"] == "DNS"
