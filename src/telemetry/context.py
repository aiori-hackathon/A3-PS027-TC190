"""
Measurement Context & Client Telemetry Collector
Captures local/public IP addresses, ASN, ISP, geolocation, and resolver telemetry.
"""

import socket
import time
import urllib.request
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class TelemetryCollector:
    """Collects environmental measurement context for the auditor."""

    @staticmethod
    def get_local_interfaces() -> Dict[str, Optional[str]]:
        """Detect local IPv4 and IPv6 interfaces."""
        res = {"ipv4": None, "ipv6": None}
        try:
            s4 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s4.settimeout(1.5)
            s4.connect(("8.8.8.8", 80))
            res["ipv4"] = s4.getsockname()[0]
            s4.close()
        except Exception as e:
            logger.debug(f"Local IPv4 detection failed: {e}")

        try:
            s6 = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            s6.settimeout(1.5)
            s6.connect(("2001:4860:4860::8888", 80))
            res["ipv6"] = s6.getsockname()[0]
            s6.close()
        except Exception as e:
            logger.debug(f"Local IPv6 detection failed: {e}")

        return res

    _cached_telemetry: Optional[Dict[str, Any]] = None
    _cache_timestamp: float = 0.0

    @classmethod
    def get_public_ip_telemetry(cls) -> Dict[str, Any]:
        """Fetch public IP, ASN, ISP, and Geolocation metadata with resilient multi-provider fallback and caching."""
        current_time = time.time()
        if cls._cached_telemetry and (current_time - cls._cache_timestamp < 600):
            return dict(cls._cached_telemetry)

        telemetry: Dict[str, Any] = {
            "public_ipv4": None,
            "public_ipv6": None,
            "asn": None,
            "as_org": None,
            "city": None,
            "country": None,
            "country_code": None
        }

        # 1. Query IPv4 public IP
        try:
            req = urllib.request.Request(
                "https://api.ipify.org?format=json",
                headers={"User-Agent": "Mozilla/5.0 (compatible; AIORI-PS027-Auditor/1.0)"}
            )
            with urllib.request.urlopen(req, timeout=2.5) as r:
                data = json.loads(r.read().decode())
                telemetry["public_ipv4"] = data.get("ip")
        except Exception as e:
            logger.debug(f"Public IPv4 probe failed: {e}")

        # 2. Query IPv6 public IP
        try:
            req6 = urllib.request.Request(
                "https://api64.ipify.org?format=json",
                headers={"User-Agent": "Mozilla/5.0 (compatible; AIORI-PS027-Auditor/1.0)"}
            )
            with urllib.request.urlopen(req6, timeout=2.5) as r:
                data = json.loads(r.read().decode())
                ip = data.get("ip")
                if ":" in str(ip):
                    telemetry["public_ipv6"] = ip
        except Exception as e:
            logger.debug(f"Public IPv6 probe failed: {e}")

        # 3. Query ASN and Geo data via resilient multi-provider fallback
        # Tier A: ipwho.is (SSL, high accuracy, includes ASN and ISP)
        geo_resolved = False
        try:
            target_ip_arg = telemetry["public_ipv4"] if telemetry["public_ipv4"] else ""
            req_geo = urllib.request.Request(
                f"https://ipwho.is/{target_ip_arg}",
                headers={"User-Agent": "Mozilla/5.0 (compatible; AIORI-PS027-Auditor/1.0)"}
            )
            with urllib.request.urlopen(req_geo, timeout=3.0) as r:
                geo = json.loads(r.read().decode())
                if geo.get("success"):
                    conn = geo.get("connection", {})
                    asn_num = conn.get("asn")
                    telemetry["asn"] = f"AS{asn_num}" if asn_num and not str(asn_num).startswith("AS") else str(asn_num) if asn_num else None
                    telemetry["as_org"] = conn.get("org") or conn.get("isp")
                    telemetry["city"] = geo.get("city")
                    telemetry["country"] = geo.get("country")
                    telemetry["country_code"] = geo.get("country_code")
                    if not telemetry["public_ipv4"] and geo.get("ip") and ":" not in geo.get("ip"):
                        telemetry["public_ipv4"] = geo.get("ip")
                    geo_resolved = bool(telemetry["asn"] or telemetry["city"])
        except Exception as e:
            logger.debug(f"ipwho.is probe failed: {e}")

        # Tier B: ip-api.com (reliable fallback if Tier A is unreachable)
        if not geo_resolved:
            try:
                target_ip_arg = telemetry["public_ipv4"] if telemetry["public_ipv4"] else ""
                req_geo2 = urllib.request.Request(
                    f"http://ip-api.com/json/{target_ip_arg}",
                    headers={"User-Agent": "Mozilla/5.0 (compatible; AIORI-PS027-Auditor/1.0)"}
                )
                with urllib.request.urlopen(req_geo2, timeout=3.0) as r:
                    geo = json.loads(r.read().decode())
                    if geo.get("status") == "success":
                        asn_str = geo.get("as", "")
                        parts = asn_str.split(" ", 1)
                        telemetry["asn"] = parts[0] if parts else None
                        telemetry["as_org"] = parts[1] if len(parts) > 1 else geo.get("org") or geo.get("isp")
                        telemetry["city"] = geo.get("city")
                        telemetry["country"] = geo.get("country")
                        telemetry["country_code"] = geo.get("countryCode")
                        if not telemetry["public_ipv4"] and geo.get("query"):
                            telemetry["public_ipv4"] = geo.get("query")
                        geo_resolved = True
            except Exception as e:
                logger.debug(f"ip-api.com probe failed: {e}")

        # Tier C: ipapi.co (final fallback)
        if not geo_resolved:
            try:
                req_geo3 = urllib.request.Request(
                    "https://ipapi.co/json/",
                    headers={"User-Agent": "Mozilla/5.0 (compatible; AIORI-PS027-Auditor/1.0)"}
                )
                with urllib.request.urlopen(req_geo3, timeout=3.0) as r:
                    geo = json.loads(r.read().decode())
                    if not geo.get("error"):
                        telemetry["asn"] = geo.get("asn")
                        telemetry["as_org"] = geo.get("org")
                        telemetry["city"] = geo.get("city")
                        telemetry["country"] = geo.get("country_name")
                        telemetry["country_code"] = geo.get("country_code")
            except Exception as e:
                logger.debug(f"ipapi.co probe failed: {e}")

        cls._cached_telemetry = dict(telemetry)
        cls._cache_timestamp = current_time
        return telemetry

    @staticmethod
    def get_system_resolvers() -> Dict[str, Any]:
        """Discover active DNS nameservers from system configuration and measure RTT."""
        nameservers = []
        try:
            with open("/etc/resolv.conf", "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("nameserver"):
                        parts = line.split()
                        if len(parts) > 1:
                            nameservers.append(parts[1])
        except Exception as e:
            logger.debug(f"Reading /etc/resolv.conf failed: {e}")

        if not nameservers:
            nameservers = ["1.1.1.1", "8.8.8.8"]

        # Measure RTT to primary resolver
        latency_ms = None
        if nameservers:
            target = nameservers[0]
            try:
                t0 = time.perf_counter()
                s = socket.socket(socket.AF_INET6 if ":" in target else socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(1.0)
                s.connect((target, 53))
                s.close()
                latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            except Exception:
                pass

        return {
            "nameservers": nameservers,
            "primary_resolver": nameservers[0] if nameservers else None,
            "resolver_latency_ms": latency_ms
        }

    @classmethod
    def get_full_context(cls) -> Dict[str, Any]:
        """Aggregate complete measurement context."""
        local = cls.get_local_interfaces()
        public = cls.get_public_ip_telemetry()
        dns = cls.get_system_resolvers()

        return {
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "local_interfaces": local,
            "has_native_ipv6": local["ipv6"] is not None,
            "public_telemetry": public,
            "dns_telemetry": dns
        }


# Quick test helper
if __name__ == "__main__":
    import pprint
    pprint.pprint(TelemetryCollector.get_full_context())
