"""
Stage 2: TCP Handshake Diagnostic
Executes direct socket connections over IPv6 and IPv4, measuring RTT and isolating failure modes.
"""

import socket
import time
import errno
import logging
from typing import Dict, Any, Optional, Tuple

from ..config import TCP_TIMEOUT

logger = logging.getLogger(__name__)

class TCPDiagnostic:
    """Performs raw TCP socket connection diagnostics over IPv6 and IPv4."""

    def __init__(self, timeout: float = TCP_TIMEOUT):
        self.timeout = timeout

    def diagnose_ipv6(
        self,
        ipv6_addr: str,
        port: int = 443,
        return_socket: bool = False
    ) -> Tuple[Dict[str, Any], Optional[socket.socket]]:
        """
        Attempt a raw TCP connection to an IPv6 address.
        Optionally returns the active socket for reuse in TLS negotiation.
        """
        t0 = time.perf_counter()
        result: Dict[str, Any] = {
            "stage": "TCP_IPV6",
            "target_ip": ipv6_addr,
            "port": port,
            "status": "UNKNOWN",
            "rtt_ms": 0.0,
            "error_code": None,
            "error_detail": None,
        }

        sock = None
        try:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            # Connect to (host, port, flowinfo, scope_id)
            sock.connect((ipv6_addr, port, 0, 0))
            
            rtt_ms = round((time.perf_counter() - t0) * 1000, 2)
            result["status"] = "TCP_SUCCESS"
            result["rtt_ms"] = rtt_ms
            
            if return_socket:
                return result, sock
            else:
                sock.close()
                return result, None

        except socket.timeout:
            result["status"] = "TCP_TIMEOUT"
            result["error_code"] = "ETIMEDOUT"
            result["error_detail"] = f"TCP handshake to [{ipv6_addr}]:{port} timed out after {self.timeout}s (Firewall/Blackhole)"
        except ConnectionRefusedError:
            result["status"] = "TCP_CONN_REFUSED"
            result["error_code"] = "ECONNREFUSED"
            result["error_detail"] = f"Connection refused on port {port} at [{ipv6_addr}]"
        except OSError as e:
            err_code = e.errno
            if err_code in (errno.ENETUNREACH, getattr(errno, "EHOSTUNREACH", 65)):
                result["status"] = "TCP_NO_ROUTE"
                result["error_code"] = "ENETUNREACH/EHOSTUNREACH"
                result["error_detail"] = f"No route to host [{ipv6_addr}]: {e.strerror}"
            else:
                result["status"] = "TCP_ERROR"
                result["error_code"] = str(err_code)
                result["error_detail"] = f"Socket error connecting to [{ipv6_addr}]:{port} - {e}"
        except Exception as e:
            result["status"] = "TCP_ERROR"
            result["error_detail"] = f"Unexpected TCP failure: {e}"

        result["rtt_ms"] = round((time.perf_counter() - t0) * 1000, 2)
        if sock:
            try:
                sock.close()
            except Exception:
                pass

        return result, None

    def diagnose_ipv4(self, ipv4_addr: str, port: int = 443) -> Dict[str, Any]:
        """Attempt TCP connection over IPv4 baseline."""
        t0 = time.perf_counter()
        result: Dict[str, Any] = {
            "stage": "TCP_IPV4",
            "target_ip": ipv4_addr,
            "port": port,
            "status": "UNKNOWN",
            "rtt_ms": 0.0,
            "error_detail": None,
        }

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((ipv4_addr, port))
            sock.close()
            result["status"] = "TCP_SUCCESS"
            result["rtt_ms"] = round((time.perf_counter() - t0) * 1000, 2)
        except Exception as e:
            result["status"] = "TCP_FAIL"
            result["error_detail"] = str(e)
            result["rtt_ms"] = round((time.perf_counter() - t0) * 1000, 2)

        return result
