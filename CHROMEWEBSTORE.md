# Chrome Web Store Listing & Compliance

## Extension Metadata
- **Name**: IPv6 Readiness Auditor
- **Version**: 1.0.0
- **Category**: Developer Tools / Network & Performance
- **Short Description**: Full in-browser IPv6 website & dependency readiness auditor with live topology DAG, 4-stage OSI diagnostics, and national benchmark.
- **Detailed Description**:
  IPv6 Readiness Auditor is a complete, native in-browser application that analyzes the real-world IPv6 reachability of websites and all their sub-resource dependencies directly inside Google Chrome via the Side Panel API.

  Designed as a standalone alternative to web measurement portals, the auditor allows developers, sysadmins, and network engineers to diagnose dual-stack readiness alongside any active browsing session without switching tabs.

  Key Features:
  - Native Side Panel Integration: Docks side-by-side with your active browser tab with zero tab switching.
  - 1-Click Active Tab Audit: Instantly measures the IPv6 compliance of your current webpage.
  - 4-Stage OSI Protocol Diagnostics: Deep failure isolation across DNS (AAAA/A), TCP SYN/ACK, TLSv1.3/ALPN, and HTTP GET payload delivery.
  - Interactive Canvas 2D Topology DAG: Visualizes apex roots, first-party assets, and third-party dependencies with live particle packet flow.
  - Root Cause Isolation & Remediation: Plain-English explanations and actionable remediation steps based on RFC 8305 and RFC 4038.
  - 30-Site National Benchmark: Empirical analysis of India's digital infrastructure across Government, Education, and Commerce sectors with CSV/JSON exports.
  - Controlled Testbed Suite: Deterministic ground-truth verification across 8 synthetic protocol scenarios with 100% precision and recall.
  - Client Dual-Stack Telemetry: Measures client IP, ASN, ISP, and Happy Eyeballs v2 connection preference.

---

## Permissions Justification

| Permission | Technical Requirement & Justification |
| :--- | :--- |
| `sidePanel` | Required to provide a docked, native application interface on the right side of the active browser window, eliminating external tab dependency. |
| `webRequest` | Required to read the remote server IP address (`details.ip`) of HTTP/HTTPS requests to evaluate whether subresources load over IPv6 or IPv4. |
| `tabs` | Required to detect the active tab's domain and URL for the 1-click active tab audit and toolbar badge updates. |
| `storage` | Required to cache session diagnostic traces and benchmark data in `chrome.storage.session` and `chrome.storage.local`. |
| `activeTab` | Required to interact directly with the active browsing session upon user invocation. |
| `host_permissions` (`<all_urls>`) | Required because modern web applications retrieve subresource dependencies (scripts, styles, APIs, CDNs) from arbitrary third-party domains worldwide. |

---

## Privacy & Data Use Disclosures
- **Data Collection**: None. The extension does not collect, log, sell, or transmit personal data, browsing history, or user identifiers.
- **Data Processing**: All network socket measurements and IP address evaluations occur strictly in-memory on the user's local machine.
- **Remote Communications**: The extension makes zero external tracking calls. Network socket probes are executed locally or against the user's configured local auditor API daemon.
