"""
Stage 4: HTTP Retrieval Diagnostic
Transmits HTTP/1.1 GET/HEAD requests strictly over IPv6 transport, measuring TTFB and validating status codes.
"""

import time
import socket
import ssl
import logging
from urllib.parse import urlparse
from typing import Dict, Any, Optional

from ..config import HTTP_TIMEOUT, DEFAULT_USER_AGENT

logger = logging.getLogger(__name__)

class HTTPDiagnostic:
    """Diagnoses HTTP layer retrieval strictly over IPv6."""

    def __init__(self, timeout: float = HTTP_TIMEOUT):
        self.timeout = timeout

    def diagnose_ipv6(
        self,
        url: str,
        ipv6_addr: str,
        existing_ssl_socket: Optional[ssl.SSLSocket] = None,
        existing_tcp_socket: Optional[socket.socket] = None
    ) -> Dict[str, Any]:
        """
        Execute an HTTP request over verified IPv6 transport and measure TTFB.
        """
        t0 = time.perf_counter()
        parsed = urlparse(url)
        scheme = parsed.scheme.lower() or "https"
        host = parsed.netloc.split(":")[0]
        port = parsed.port or (443 if scheme == "https" else 80)
        path = parsed.path or "/"
        if parsed.query:
            path += f"?{parsed.query}"

        result: Dict[str, Any] = {
            "stage": "HTTP_IPV6",
            "url": url,
            "target_ip": ipv6_addr,
            "status": "UNKNOWN",
            "http_status_code": None,
            "status_line": None,
            "content_type": None,
            "content_length": None,
            "ttfb_ms": 0.0,
            "error_detail": None,
        }

        sock = None
        needs_close = True

        try:
            if existing_ssl_socket:
                sock = existing_ssl_socket
                needs_close = False
            elif existing_tcp_socket and scheme == "http":
                sock = existing_tcp_socket
                needs_close = False
            else:
                # Create connection
                raw_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
                raw_sock.settimeout(self.timeout)
                raw_sock.connect((ipv6_addr, port, 0, 0))

                if scheme == "https":
                    ctx = ssl.create_default_context()
                    sock = ctx.wrap_socket(raw_sock, server_hostname=host)
                else:
                    sock = raw_sock

            sock.settimeout(self.timeout)

            # Send minimal HTTP request
            request_data = (
                f"GET {path} HTTP/1.1\r\n"
                f"Host: {host}\r\n"
                f"User-Agent: {DEFAULT_USER_AGENT}\r\n"
                f"Accept: */*\r\n"
                f"Connection: close\r\n\r\n"
            ).encode("utf-8")

            t_send = time.perf_counter()
            sock.sendall(request_data)

            # Read response head for TTFB
            raw_response = b""
            while b"\r\n\r\n" not in raw_response and len(raw_response) < 65536:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                raw_response += chunk

            ttfb_ms = round((time.perf_counter() - t_send) * 1000, 2)
            result["ttfb_ms"] = ttfb_ms

            if not raw_response:
                result["status"] = "HTTP_EMPTY_RESPONSE"
                result["error_detail"] = "Server closed socket without sending HTTP response headers"
                return result

            # Parse headers
            header_data = raw_response.split(b"\r\n\r\n")[0].decode("iso-8859-1", errors="replace")
            lines = header_data.split("\r\n")
            if lines:
                status_line = lines[0]
                result["status_line"] = status_line
                parts = status_line.split(" ", 2)
                if len(parts) >= 2 and parts[1].isdigit():
                    code = int(parts[1])
                    result["http_status_code"] = code

                    for line in lines[1:]:
                        if ":" in line:
                            k, v = line.split(":", 1)
                            k = k.strip().lower()
                            v = v.strip()
                            if k == "content-type":
                                result["content_type"] = v
                            elif k == "content-length" and v.isdigit():
                                result["content_length"] = int(v)

                    # Classify outcome
                    if 200 <= code < 400:
                        result["status"] = "HTTP_SUCCESS"
                    elif 400 <= code < 500:
                        result["status"] = "HTTP_4XX_CLIENT_ERROR"
                        result["error_detail"] = f"Client error response ({code})"
                    elif 500 <= code < 600:
                        result["status"] = "HTTP_5XX_SERVER_ERROR"
                        result["error_detail"] = f"Server error response ({code}) over IPv6"
                    else:
                        result["status"] = f"HTTP_{code}"

        except socket.timeout:
            result["status"] = "HTTP_TIMEOUT"
            result["error_detail"] = f"HTTP request timed out after {self.timeout}s"
        except ConnectionResetError:
            result["status"] = "HTTP_RESET"
            result["error_detail"] = "Connection reset by peer during HTTP exchange"
        except Exception as e:
            result["status"] = "HTTP_ERROR"
            result["error_detail"] = f"HTTP exchange failed: {e}"
        finally:
            if needs_close and sock:
                try:
                    sock.close()
                except Exception:
                    pass

        return result
