"""
Stage 3: TLS Negotiation Diagnostic
Wraps IPv6 TCP transport with TLS, enforces SNI validation, and verifies certificate chains.
"""

import ssl
import socket
import time
import logging
from typing import Dict, Any, Optional, Tuple

from ..config import TLS_TIMEOUT

logger = logging.getLogger(__name__)

class TLSDiagnostic:
    """Performs TLS handshake diagnostics with SNI verification over IPv6."""

    def __init__(self, timeout: float = TLS_TIMEOUT):
        self.timeout = timeout

    def diagnose_ipv6(
        self,
        hostname: str,
        ipv6_addr: str,
        port: int = 443,
        existing_socket: Optional[socket.socket] = None,
        return_socket: bool = False
    ) -> Tuple[Dict[str, Any], Optional[ssl.SSLSocket]]:
        """
        Perform TLS handshake over IPv6 for the given hostname and IP.
        """
        t0 = time.perf_counter()
        result: Dict[str, Any] = {
            "stage": "TLS_IPV6",
            "hostname": hostname,
            "target_ip": ipv6_addr,
            "port": port,
            "status": "UNKNOWN",
            "tls_version": None,
            "cipher": None,
            "cert_subject": None,
            "cert_issuer": None,
            "cert_expires": None,
            "latency_ms": 0.0,
            "error_detail": None,
        }

        sock = existing_socket
        ssl_sock = None

        try:
            if sock is None:
                sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                sock.connect((ipv6_addr, port, 0, 0))

            context = ssl.create_default_context()
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED

            # Wrap socket and perform handshake with SNI
            t_tls_start = time.perf_counter()
            ssl_sock = context.wrap_socket(sock, server_hostname=hostname)
            ssl_sock.settimeout(self.timeout)

            # Extract certificate and cipher details
            cert = ssl_sock.getpeercert()
            cipher = ssl_sock.cipher()
            tls_version = ssl_sock.version()

            result["status"] = "TLS_SUCCESS"
            result["tls_version"] = tls_version
            result["cipher"] = cipher[0] if cipher else None
            result["latency_ms"] = round((time.perf_counter() - t_tls_start) * 1000, 2)

            if cert:
                result["cert_expires"] = cert.get("notAfter")
                # Parse subject and issuer common names
                for field in cert.get("subject", ()):
                    for k, v in field:
                        if k == "commonName":
                            result["cert_subject"] = v
                for field in cert.get("issuer", ()):
                    for k, v in field:
                        if k == "commonName":
                            result["cert_issuer"] = v

            if return_socket:
                return result, ssl_sock
            else:
                ssl_sock.close()
                return result, None

        except ssl.SSLCertVerificationError as e:
            err_msg = str(e)
            if "hostname" in err_msg.lower() or "doesn't match" in err_msg.lower():
                result["status"] = "TLS_HOSTNAME_MISMATCH"
                result["error_detail"] = f"SSL Certificate hostname mismatch for '{hostname}' on [{ipv6_addr}]: {e.verify_message}"
            elif "expired" in err_msg.lower() or "notAfter" in err_msg.lower():
                result["status"] = "TLS_CERT_EXPIRED"
                result["error_detail"] = f"SSL Certificate expired for '{hostname}' on [{ipv6_addr}]"
            else:
                result["status"] = "TLS_CERT_INVALID"
                result["error_detail"] = f"SSL Certificate verification failed: {e.verify_message}"
        except ssl.SSLError as e:
            result["status"] = "TLS_HANDSHAKE_FAIL"
            result["error_detail"] = f"SSL Handshake failure on [{ipv6_addr}]: {e}"
        except socket.timeout:
            result["status"] = "TLS_TIMEOUT"
            result["error_detail"] = f"TLS handshake timed out after {self.timeout}s"
        except Exception as e:
            result["status"] = "TLS_ERROR"
            result["error_detail"] = f"TLS unexpected error: {e}"

        result["latency_ms"] = round((time.perf_counter() - t0) * 1000, 2)
        if ssl_sock:
            try:
                ssl_sock.close()
            except Exception:
                pass
        elif sock:
            try:
                sock.close()
            except Exception:
                pass

        return result, None
