"""
Controlled Testbed Ground Truth Manifest
Defines seeded test assets and expected protocol failure stages.
"""

from typing import Dict, Any

# Ground Truth seeded test assets on the controlled site
CONTROLLED_GROUND_TRUTH: Dict[str, Dict[str, Any]] = {
    "valid_dualstack_js": {
        "url_path": "/static/valid-dualstack.js",
        "expected_status": "FULL_IPV6_READY",
        "expected_failure_stage": None,
        "is_seeded_failure": False,
        "description": "Dual-stack compliant JavaScript file"
    },
    "valid_dualstack_css": {
        "url_path": "/static/valid-dualstack.css",
        "expected_status": "FULL_IPV6_READY",
        "expected_failure_stage": None,
        "is_seeded_failure": False,
        "description": "Dual-stack compliant CSS stylesheet"
    },
    "seeded_ipv4_only_script": {
        "url_path": "/static/seeded-ipv4-only.js",
        "mock_domain": "ipv4only.testbed.internal",
        "expected_status": "IPV4_ONLY_DEPENDENCY",
        "expected_failure_stage": "DNS",
        "is_seeded_failure": True,
        "description": "Deliberately seeded IPv4-only script (No AAAA record)"
    },
    "seeded_ipv4_only_css": {
        "url_path": "/static/seeded-ipv4-only.css",
        "mock_domain": "legacy-cdn.testbed.internal",
        "expected_status": "IPV4_ONLY_DEPENDENCY",
        "expected_failure_stage": "DNS",
        "is_seeded_failure": True,
        "description": "Deliberately seeded IPv4-only stylesheet (No AAAA record)"
    },
    "seeded_ipv4_only_img": {
        "url_path": "/static/seeded-ipv4-only.png",
        "mock_domain": "static-v4.testbed.internal",
        "expected_status": "IPV4_ONLY_DEPENDENCY",
        "expected_failure_stage": "DNS",
        "is_seeded_failure": True,
        "description": "Deliberately seeded IPv4-only image banner (No AAAA record)"
    },
    "seeded_broken_tcp_v6": {
        "url_path": "/mock/broken-tcp.js",
        "mock_domain": "blackhole-v6.testbed.internal",
        "expected_status": "BROKEN_IPV6_TCP",
        "expected_failure_stage": "TCP",
        "is_seeded_failure": True,
        "description": "Seeded broken IPv6 TCP routing (AAAA resolves to unroutable 100::1)"
    },
    "seeded_broken_tls_v6": {
        "url_path": "/mock/broken-tls.js",
        "mock_domain": "badssl-v6.testbed.internal",
        "expected_status": "BROKEN_IPV6_TLS",
        "expected_failure_stage": "TLS",
        "is_seeded_failure": True,
        "description": "Seeded broken IPv6 TLS negotiation (Certificate hostname mismatch)"
    },
    "seeded_broken_http_v6": {
        "url_path": "/mock/broken-http-500.json",
        "mock_domain": "error500-v6.testbed.internal",
        "expected_status": "BROKEN_IPV6_HTTP",
        "expected_failure_stage": "HTTP",
        "is_seeded_failure": True,
        "description": "Seeded broken IPv6 HTTP retrieval (Server returns HTTP 500 over IPv6)"
    }
}
