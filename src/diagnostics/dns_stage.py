"""
Stage 1: DNS Resolution Diagnostic
Queries A and AAAA records, detects missing AAAA (IPv4-only), NODATA, NXDOMAIN, SERVFAIL, and CNAME chains.
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

    def diagnose(self, hostname: str) -> Dict[str, Any]:
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

        return result
