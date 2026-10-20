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

    @staticmethod
    def get_public_ip_telemetry() -> Dict[str, Any]:
        """Fetch public IP, ASN, ISP, and Geolocation metadata."""
        telemetry: Dict[str, Any] = {
            "public_ipv4": None,
            "public_ipv6": None,
            "asn": None,
            "as_org": None,
            "city": None,
            "country": None,
            "country_code": None
        }

        # Query IPv4 public IP
        try:
            req = urllib.request.Request(
                "https://api.ipify.org?format=json",
                headers={"User-Agent": "AIORI-PS027-Auditor/1.0"}
            )
            with urllib.request.urlopen(req, timeout=2.5) as r:
                data = json.loads(r.read().decode())
                telemetry["public_ipv4"] = data.get("ip")
        except Exception as e:
            logger.debug(f"Public IPv4 probe failed: {e}")

        # Query IPv6 public IP
        try:
            req6 = urllib.request.Request(
                "https://api64.ipify.org?format=json",
                headers={"User-Agent": "AIORI-PS027-Auditor/1.0"}
            )
            with urllib.request.urlopen(req6, timeout=2.5) as r:
                data = json.loads(r.read().decode())
                ip = data.get("ip")
                if ":" in ip:
                    telemetry["public_ipv6"] = ip
        except Exception as e:
            logger.debug(f"Public IPv6 probe failed: {e}")

        # Query ASN and Geo data via ipwhois/ip-api
        try:
            req_geo = urllib.request.Request(
                "https://ipapi.co/json/",
                headers={"User-Agent": "AIORI-PS027-Auditor/1.0"}
            )
            with urllib.request.urlopen(req_geo, timeout=3.0) as r:
                geo = json.loads(r.read().decode())
                telemetry["asn"] = geo.get("asn")
                telemetry["as_org"] = geo.get("org")
                telemetry["city"] = geo.get("city")
                telemetry["country"] = geo.get("country_name")
                telemetry["country_code"] = geo.get("country_code")
        except Exception as e:
            logger.debug(f"Geo/ASN probe fallback: {e}")

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
