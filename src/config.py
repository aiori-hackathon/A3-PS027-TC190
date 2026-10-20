"""
Global Configuration and Constants for PS-027 Auditor
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
REPORTS_DIR = BASE_DIR / "reports"
DOCS_DIR = BASE_DIR / "docs"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

# Server Ports
API_PORT = 8000
TESTBED_PORT = 8888
API_HOST = "0.0.0.0"
TESTBED_HOST = "0.0.0.0"

# Timeouts (seconds)
DNS_TIMEOUT = 2.5
TCP_TIMEOUT = 3.0
TLS_TIMEOUT = 3.5
HTTP_TIMEOUT = 5.0
BROWSER_NAV_TIMEOUT = 25000  # ms
BROWSER_SETTLE_MS = 3000     # ms

# Concurrency
MAX_CONCURRENT_PROBES = 25

# User Agent
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 "
    "AIORI-PS027-Auditor/1.0"
)

# Public DNS Resolvers for Fallback Probing
PUBLIC_DNS_RESOLVERS = [
    "1.1.1.1",              # Cloudflare IPv4
    "2606:4700:4700::1111", # Cloudflare IPv6
    "8.8.8.8",              # Google IPv4
    "2001:4860:4860::8888"  # Google IPv6
]

# Blast Radius Resource Criticality Weights (0.0 to 1.0)
RESOURCE_CRITICALITY_WEIGHTS = {
    "document": 1.0,     # Root document failure = 100% breakage
    "stylesheet": 0.85,   # Render-blocking styles
    "script": 0.85,       # Application code & runtime logic
    "fetch": 0.75,        # API / data exchange
    "xhr": 0.75,          # Asynchronous data
    "font": 0.50,         # Visual typography
    "image": 0.30,        # Graphic asset (graceful degradation)
    "media": 0.30,        # Video / Audio
    "websocket": 0.70,    # Real-time socket
    "other": 0.20         # Tracking pixels, beacons, etc.
}

# 30 Selected Websites Categories
BENCHMARK_SECTORS = [
    "Government & Public Services",
    "E-Commerce & Retail",
    "News & Media",
    "Higher Education & Research",
    "SaaS, Cloud & Big Tech",
    "Banking & Financial Core"
]
