"""
Stage 1: DNS Resolution Diagnostic
Queries A and AAAA records, detects missing AAAA (IPv4-only), NODATA, NXDOMAIN, SERVFAIL, and CNAME chains.
Includes Authoritative Nameserver (NS) IPv6 Parity audit (RFC 3901).
"""

import time
import logging
from typing import Dict, Any, List
import dns.resolver
import dns.exception

from ..config import DNS_TIMEOUT, PUBLIC_DNS_RESOLVERS

logger = logging.getLogger(__name__)

class DNSDiagnostic:
    """Performs isolated DNS diagnosis on a given hostname."""

    def __init__(self, timeout: float = DNS_TIMEOUT):
        self.timeout = timeout
        self.resolver = dns.resolver.Resolver()
        self.resolver.lifetime = timeout
        self.resolver.timeout = timeout

    @staticmethod
    def get_apex_domain(hostname: str) -> str:
        """Extracts likely apex zone domain from hostname, handling two-level TLDs."""
        parts = hostname.strip().lower().split(".")
        if len(parts) <= 2:
            return ".".join(parts)
        second_level_tlds = {
            "gov.in", "nic.in", "co.in", "ac.in", "res.in", "edu.in", "net.in",
            "co.uk", "org.uk", "com.au", "net.au", "co.nz", "com.br", "co.jp"
        }
        if len(parts) >= 3 and f"{parts[-2]}.{parts[-1]}" in second_level_tlds:
            return ".".join(parts[-3:])
        return ".".join(parts[-2:])

    def diagnose_nameservers(self, hostname: str) -> Dict[str, Any]:
        """
        Audits authoritative nameservers for IPv6 parity (RFC 3901).
        Checks if nameservers have AAAA records so IPv6-only resolvers can reach them.
        """
        apex = self.get_apex_domain(hostname)
        result: Dict[str, Any] = {
            "apex_domain": apex,
            "total_nameservers": 0,
            "ipv6_nameservers_count": 0,
            "ipv4_nameservers_count": 0,
            "has_ipv6_ns": False,
            "rfc3901_compliant": False,
            "status": "UNKNOWN",
            "nameservers": [],
            "error": None
        }

        try:
            ns_ans = self.resolver.resolve(apex, "NS")
            server_names = [str(r.target).rstrip(".") for r in ns_ans]
        except Exception as e:
            result["error"] = f"Failed to resolve NS records: {type(e).__name__}"
            result["status"] = "LOOKUP_FAILED"
            return result

        result["total_nameservers"] = len(server_names)
        details = []
        v6_count = 0
        v4_count = 0

        for ns_name in server_names[:8]:
            v6_ips = []
            v4_ips = []
            # Check AAAA
            try:
                a6 = self.resolver.resolve(ns_name, "AAAA")
                v6_ips = [r.to_text() for r in a6]
            except Exception:
                pass
            # Check A
            try:
                a4 = self.resolver.resolve(ns_name, "A")
                v4_ips = [r.to_text() for r in a4]
            except Exception:
                pass

            if v6_ips:
                v6_count += 1
            if v4_ips:
                v4_count += 1

            details.append({
                "host": ns_name,
                "has_aaaa": bool(v6_ips),
                "has_a": bool(v4_ips),
                "ipv6_addresses": v6_ips,
                "ipv4_addresses": v4_ips
            })

        result["ipv6_nameservers_count"] = v6_count
        result["ipv4_nameservers_count"] = v4_count
        result["has_ipv6_ns"] = v6_count > 0
        result["nameservers"] = details

        # RFC 3901 guideline: At least two authoritative nameservers with IPv6 transport
        is_compliant = (v6_count >= 2) or (len(server_names) > 0 and v6_count == len(server_names))
        result["rfc3901_compliant"] = is_compliant

        if is_compliant:
            result["status"] = "RFC3901_COMPLIANT"
        elif v6_count > 0:
            result["status"] = "PARTIAL_V6_NS"
        else:
            result["status"] = "NO_IPV6_NS"

        return result

    def diagnose(self, hostname: str, check_ns: bool = False) -> Dict[str, Any]:
        """
        Diagnose DNS records for a given hostname.
        Returns detailed record information and stage status.
        """
        t0 = time.perf_counter()
        
        result: Dict[str, Any] = {
            "stage": "DNS",
            "hostname": hostname,
            "status": "UNKNOWN",
            "has_aaaa": False,
            "has_a": False,
            "aaaa_records": [],
            "a_records": [],
            "cname_chain": [],
            "ttl": None,
            "latency_ms": 0.0,
            "error_detail": None,
        }

        # Clean hostname
        host = hostname.strip().lower()
        if host.startswith("http://") or host.startswith("https://"):
            from urllib.parse import urlparse
            host = urlparse(host).netloc.split(":")[0]
        else:
            host = host.split(":")[0]

        result["hostname"] = host

        # 1. Query AAAA (IPv6)
        try:
            t_start = time.perf_counter()
            aaaa_ans = self.resolver.resolve(host, "AAAA")
            result["aaaa_records"] = [r.to_text() for r in aaaa_ans]
            result["has_aaaa"] = len(result["aaaa_records"]) > 0
            if aaaa_ans.rrset:
                result["ttl"] = aaaa_ans.rrset.ttl
                if str(aaaa_ans.canonical_name).rstrip(".") != host:
                    result["cname_chain"].append(str(aaaa_ans.canonical_name).rstrip("."))
        except dns.resolver.NoAnswer:
            result["has_aaaa"] = False
        except dns.resolver.NXDOMAIN:
            result["status"] = "NXDOMAIN"
            result["error_detail"] = "Domain name does not exist"
            result["latency_ms"] = round((time.perf_counter() - t0) * 1000, 2)
            if check_ns:
                result["ns_audit"] = self.diagnose_nameservers(host)
            return result
        except dns.exception.Timeout:
            result["error_detail"] = "DNS query timed out"
        except Exception as e:
            result["error_detail"] = f"DNS AAAA query failed: {type(e).__name__}"

        # 2. Query A (IPv4)
        try:
            a_ans = self.resolver.resolve(host, "A")
            result["a_records"] = [r.to_text() for r in a_ans]
            result["has_a"] = len(result["a_records"]) > 0
            if not result["ttl"] and a_ans.rrset:
                result["ttl"] = a_ans.rrset.ttl
            if str(a_ans.canonical_name).rstrip(".") != host:
                cname = str(a_ans.canonical_name).rstrip(".")
                if cname not in result["cname_chain"]:
                    result["cname_chain"].append(cname)
        except dns.resolver.NoAnswer:
            result["has_a"] = False
        except dns.resolver.NXDOMAIN:
            result["status"] = "NXDOMAIN"
            result["error_detail"] = "Domain name does not exist"
            result["latency_ms"] = round((time.perf_counter() - t0) * 1000, 2)
            if check_ns:
                result["ns_audit"] = self.diagnose_nameservers(host)
            return result
        except dns.exception.Timeout:
            pass
        except Exception:
            pass

        result["latency_ms"] = round((time.perf_counter() - t0) * 1000, 2)

        # 3. Classify Stage Outcome
        if result["has_aaaa"]:
            result["status"] = "AAAA_EXISTS"
        elif result["has_a"] and not result["has_aaaa"]:
            result["status"] = "NO_AAAA"
            result["error_detail"] = "Apex/Host has IPv4 (A) record but lacks IPv6 (AAAA) record"
        elif not result["has_a"] and not result["has_aaaa"]:
            if result["error_detail"] and "timeout" in result["error_detail"].lower():
                result["status"] = "DNS_TIMEOUT"
            else:
                result["status"] = "NODATA"
                result["error_detail"] = "Domain exists but contains neither A nor AAAA records"

        if check_ns:
            result["ns_audit"] = self.diagnose_nameservers(host)

        return result
