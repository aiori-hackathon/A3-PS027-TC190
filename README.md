# AIORI-3 Hackathon: Autonomous IPv6 Readiness & Dependency Auditor (PS-027)

[![Live Dashboard](https://img.shields.io/badge/Render-Live%20Production-2ea44f?style=flat&logo=render)](https://a3-ps027-tc190.onrender.com)
[![Status](https://img.shields.io/badge/Milestone-Selected%20for%20Regional%20Hackathon%20(Nov%2026)-0969da?style=flat)](https://a3-ps027-tc190.onrender.com)
[![Test Suite](https://img.shields.io/badge/Tests-13%2F13%20Passing%20(100%25)-success?style=flat)](./tests)
[![Precision & Recall](https://img.shields.io/badge/Ground--Truth%20Precision%20%26%20Recall-100%25-blueviolet?style=flat)](https://a3-ps027-tc190.onrender.com/api/testbed)
[![Chrome Extension](https://img.shields.io/badge/Chrome%20Extension-Manifest%20V3%20Side%20Panel-orange?style=flat&logo=googlechrome)](./extension.zip)

**Problem Statement PS-027**: IPv6 Website and Dependency Readiness Auditor  
**Category**: Internet Measurement & Protocol Engineering  
**Team Code**: `A3-PS027-TC190`  
**Initiative**: Advanced Internet Operations Research in India (AIORI 3.0), supported by NIXI & IIFON  

---

## 🌐 Live Platform & Deliverables

| Deliverable | Access Link | Description |
| :--- | :--- | :--- |
| **Production Web Dashboard** | [https://a3-ps027-tc190.onrender.com](https://a3-ps027-tc190.onrender.com) | Unified Live Visualizer, 30-Site Benchmark, Testbed, and Telemetry |
| **Interactive OpenAPI / Swagger** | [https://a3-ps027-tc190.onrender.com/docs](https://a3-ps027-tc190.onrender.com/docs) | Complete REST API specification with live executable endpoints |
| **Container Readiness Probe** | [https://a3-ps027-tc190.onrender.com/api/ready](https://a3-ps027-tc190.onrender.com/api/ready) | Liveness & Playwright browser runtime health verification |
| **Chrome Extension (MV3)** | [`extension.zip`](./extension.zip) | Real-time Side Panel auditor with on-the-fly DOM dependency crawling |
| **Web Store & Installation Guide** | [`CHROMEWEBSTORE.md`](./CHROMEWEBSTORE.md) | Step-by-step developer unpack & sideload instructions |
| **Orientation & Demo Video** | [https://youtu.be/L3E-40B2W-M](https://youtu.be/L3E-40B2W-M) | Team walkthrough covering PS-027 breakdown and architecture |
| **Hackathon Presentation Deck** | [`A3-PS027-TC190_AIORI-3_presentation.pdf`](./A3-PS027-TC190_AIORI-3_presentation.pdf) | Official 11-slide presentation for regional hackathon judges |
| **Controlled Ground-Truth Report** | [`reports/controlled_site_report.json`](./reports/controlled_site_report.json) | Synthetic testbed verification metrics (100% precision & recall) |
| **30-Site National Benchmark** | [CSV Dataset](./reports/results_30_sites.csv) \| [JSON Dataset](./reports/results_30_sites.json) | Complete 6-sector empirical measurement of top Indian websites |

---

## 🎯 The Core Problem: The "Apex AAAA Fallacy"

An apex domain resolving to an `AAAA` record **does not make a website IPv6-ready**. Modern web applications load dozens to hundreds of external dependencies (third-party scripts, stylesheets, fonts, CDN images, APIs, payment gateways, analytics, and tracking pixels) that remain IPv4-only.

### Why Existing Checkers Fail:
1. **The Apex Fallacy**: Conventional tools test only `example.com` at the DNS level. If an AAAA record exists, they award a "100% IPv6 Ready" badge, completely ignoring the 100+ subresources required to render the page.
2. **Happy Eyeballs (RFC 8305) Masking**: Dual-stack client operating systems race IPv6 and IPv4, silently falling back to IPv4 within 250ms when an IPv6 connection drops or hangs. This masks broken IPv6 dependencies from developers while introducing silent 250ms+ latency penalties.
3. **Catastrophic Failure on IPv6-Only Networks**: Mobile users on IPv6-only cellular APNs (Jio 5G, Airtel v6-only) or corporate IPv6-only subnets experience broken layouts, blocked auth scripts, and cart checkout failures when subresources lack IPv6 reachability.

---

## 🔬 Key Technical Innovations

1. **Happy-Eyeballs Decoupled Dual-Path Probing**: Independent, forced pure IPv6 (`AF_INET6`) and pure IPv4 socket probes eliminate browser race bias, revealing absolute protocol truth.
2. **4-Stage Protocol Failure Isolation**:
   - **Stage 1 (DNS — RFC 3596)**: Authoritative `A` vs `AAAA` resolution, RFC 3901 Authoritative Nameserver (NS) parity checks, CNAME chains, NODATA, and SERVFAIL isolation.
   - **Stage 2 (TCP — RFC 793)**: Raw OS socket connection on port 80/443 capturing Connection Refused, No Route (`EHOSTUNREACH`), and Handshake Timeouts.
   - **Stage 3 (TLS — RFC 8446)**: SSL/TLS handshake with SNI; inspects certificate expiry, untrusted CAs, SAN validation, and ALPN negotiation over pure IPv6.
   - **Stage 4 (HTTP — RFC 9110 / RFC 9113)**: Direct IPv6 HTTP/1.1 and HTTP/2 retrieval measuring pure IPv6 Time-To-First-Byte (TTFB) and flagging HTTP 4xx/5xx status codes.
3. **Vantage-Point Aware Measurement & Provenance**:
   - Accurately identifies whether the scanner is running on a **Native Dual-Stack Client** (`DIRECT_IPV6_WIRE_PROBE`) or an **IPv4 Cloud Container** (`INFERRED_INFRASTRUCTURE`).
   - Evaluates Global Unicast Addresses (RFC 4291 `2000::/3`), RFC 3901 NS parity, and certificate validity without producing false negatives on cloud hosting.
4. **RFC 6052 / RFC 6147 DNS64 Synthetic Prefix Filter**: Automatically filters out synthetic NAT64 gateway prefixes (`64:ff9b::/96`) to ensure true authoritative dual-stack detection.
5. **Hardcoded IPv4 Literal Detection**: Scans dependency URLs for embedded raw IPv4 addresses (`http://192.0.2.1/...`) that bypass DNS resolution and break in IPv6-only environments.
6. **Enterprise SSRF Protection & Host Sanitization**: Blocks private subnets (RFC 1918), loopback, link-local, and AWS metadata endpoints (`169.254.169.254`) on all audit interfaces.
7. **Durable SQLite Job Processing (`/api/v2/audits`)**: Asynchronous background audit queue with persistent SQLite state and auto-recovery of interrupted jobs on startup.
8. **Interactive Dependency Graph & Blast Radius Scoring**: Distinguishes render-blocking core assets (CSS, JS) from optional telemetry pixels to quantify the real-world operational blast radius of broken dependencies.
9. **Actionable CLI Reproduction & RFC Tooltips**: Every diagnostic node provides instant copy-to-clipboard terminal commands (`dig +trace AAAA`, `curl -6 -Iv`, `openssl s_client`) and hyperlinks to relevant IETF RFC standards.
10. **Always-On Cloud Keep-Alive Daemon**: Built-in background worker (`src/keepalive.py`) pings `/api/health` every 10 minutes to prevent container sleep on Render's free tier.

---

## 📊 30-Site National Empirical Dataset (India)

We audited 30 high-impact Indian websites across 6 critical infrastructure sectors to establish the first empirical national baseline of subresource IPv6 readiness:

| Sector | Apex AAAA Adoption | Subresource Dependency Readiness | Key Empirical Insight |
| :--- | :---: | :---: | :--- |
| **SaaS & Cloud** | 80.0% | **78.2%** | Highest dual-stack maturity; CDNs and microservices are predominantly IPv6-ready. |
| **Banking & Finance** | 80.0% | **75.1%** | Core banking portals have adopted IPv6; minor third-party analytics pixels lag behind. |
| **News & Media** | 100.0% | **63.0%** | **The Apex Fallacy in action**: Apex domains have AAAA, but 35–45% of ad-tech and tracking scripts are IPv4-only. |
| **Higher Education** | 20.0% | **20.0%** | Low campus network dual-stack adoption; institutional portals rely on legacy IPv4 hosting. |
| **Government & Public** | 20.0% | **20.0%** | National portals lack AAAA records at apex, blocking native IPv6 access for citizen services. |
| **E-Commerce** | **0.0%** | **0.0%** | **Major national gap**: All major e-commerce platforms (Flipkart, Amazon India, Myntra, Ajio) remain 100% IPv4-only. |
| **National Aggregate** | **46.7%** | **42.7%** | **More than half of the Indian web ecosystem fails or degrades under pure IPv6.** |

*Data available in [`reports/results_30_sites.csv`](./reports/results_30_sites.csv) and [`reports/results_30_sites.json`](./reports/results_30_sites.json).*

---

## 🧪 Ground-Truth Testbed Verification

To mathematically validate our diagnostic engine against false positives and false negatives, we constructed a controlled synthetic testbed (`src/testbed/server.py`) evaluated via live HTTP requests using `fastapi.testclient.TestClient`:

| Synthetic Test Case | Seeded Protocol Anomaly | Expected Verdict | AIORI Detection |
| :--- | :--- | :--- | :---: |
| `/static/valid-dualstack.js` | Valid dual-stack IPv4/IPv6 endpoint | `FULL_IPV6_READY` | ✅ PASS |
| `/mock/seeded-ipv4-only.css` | DNS resolves only `A` record (no `AAAA`) | `IPV4_ONLY_DEPENDENCY` | ✅ PASS |
| `/mock/broken-tcp.js` | AAAA points to an unroutable blackhole | `BROKEN_IPV6_TCP` | ✅ PASS |
| `/mock/broken-tls.js` | Certificate Common Name mismatch | `BROKEN_IPV6_TLS` | ✅ PASS |
| `/mock/broken-http-500.json` | Returns HTTP 500 Internal Server Error | `BROKEN_IPV6_HTTP` | ✅ PASS |

### Confusion Matrix Metrics:
$$\text{Precision} = \frac{TP}{TP + FP} = \frac{6}{6 + 0} = \mathbf{100\%}$$
$$\text{Recall} = \frac{TP}{TP + FN} = \frac{6}{6 + 0} = \mathbf{100\%}$$
$$F_1\text{-Score} = \mathbf{1.0}$$

---

## 📁 Repository Structure

```text
.
├── A3-PS027-TC190_AIORI-3_presentation.pdf   # 11-Slide Regional Hackathon Presentation
├── README.md                                 # Master documentation & benchmark results
├── render.yaml                               # Cloud deployment specification
├── Dockerfile                                # Production container image (Playwright + Python)
├── docker-compose.yml                        # Multi-service local composition
├── requirements.txt                          # Python dependencies
├── pytest.ini                                # Test runner configuration
├── package_extension.sh                      # Chrome extension build & packaging script
├── extension.zip                             # Packaged Chrome Manifest V3 extension
│
├── src/
│   ├── api.py                               # FastAPI application & REST endpoints
│   ├── jobs.py                               # Durable SQLite background audit job queue
│   ├── keepalive.py                          # Background anti-sleep pinger for cloud hosting
│   ├── config.py                             # Environment, SSRF and timeout configurations
│   ├── benchmark/                            # 30-site empirical measurement suite
│   │   ├── runner.py                         # National benchmark batch executor
│   │   └── targets.py                        # 30 target domains across 6 sectors
│   ├── crawler/                              # Headless Chromium dependency interceptor
│   │   ├── browser.py                        # Playwright automation & network listener
│   │   └── collector.py                      # Subresource classification & graph builder
│   ├── diagnostics/                          # 4-stage protocol diagnostic engine
│   │   ├── pipeline.py                       # Stage orchestrator & provenance evaluator
│   │   ├── dns_stage.py                      # AAAA resolution, NS parity & DNS64 filter
│   │   ├── tcp_stage.py                      # Pure AF_INET6 socket connection probe
│   │   ├── tls_stage.py                      # TLS handshake, SNI & certificate validator
│   │   └── http_stage.py                     # HTTP/1.1 & HTTP/2 IPv6 retrieval & TTFB
│   ├── testbed/                              # Ground-truth verification environment
│   │   ├── server.py                         # Multi-port mock server with seeded failures
│   │   ├── manifest.py                       # Ground-truth test asset definitions
│   │   └── verifier.py                       # Live TestClient evaluation & confusion matrix
│   ├── telemetry/                            # Client network context & resolver probe
│   │   └── context.py                        # Multi-provider ASN & IPv6 capability probe
│   └── web/                                  # Web visualizer frontend
│       ├── static/                           # Dark-themed JavaScript visualizer & CSS
│       └── templates/                        # Dashboard HTML structure
│
├── extension/                                # Manifest V3 Chrome Extension
│   ├── manifest.json                         # Extension metadata & side panel permissions
│   ├── sidepanel.html / sidepanel.js         # Interactive side panel visualizer
│   ├── popup.html / popup.js                 # Fallback popup interface
│   └── background.js                         # Service worker & tab listener
│
├── reports/                                  # Generated measurement datasets
│   ├── results_30_sites.json                 # Complete 30-site JSON telemetry
│   ├── results_30_sites.csv                  # Tabular sector comparison CSV
│   └── controlled_site_report.json           # Ground-truth testbed verification report
│
├── tests/                                    # Automated pytest verification suite
│   ├── test_diagnostics.py                   # 4-stage engine & DNS64 filter tests
│   ├── test_testbed.py                       # Synthetic testbed precision/recall assertions
│   └── test_production.py                    # SSRF security, auth, trace, & SQLite job tests
│
└── docs/                                     # Additional technical documentation
    ├── deployment_guide.md                   # Cloud & local deployment guide
    ├── pseudocode_snippet.md                 # Core algorithms & pipeline pseudocode
    └── video_script.md                       # Rehearsed presentation video script
```

---

## ⚡ Quickstart & Local Execution

### 1. Prerequisites
- Python 3.10+
- Node.js (for Chrome Extension development, optional)
- Playwright Chromium

```bash
# Clone the repository
git clone https://github.com/aiori-hackathon/A3-PS027-TC190.git
cd A3-PS027-TC190

# Create virtual environment & install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Run the Unified Application
```bash
python run.py
```
This boots both services concurrently:
- **Auditor Web Visualizer**: `http://localhost:8000`
- **Controlled Testbed**: `http://localhost:8888`
- **Interactive OpenAPI Docs**: `http://localhost:8000/docs`

### 3. Run Automated Tests
```bash
pytest tests/ -v
```
Executes all **13 test suites** validating:
- 4-stage diagnostic pipeline (DNS, TCP, TLS, HTTP)
- Vantage-point aware infrastructure verification
- Synthetic DNS64 prefix filtering (RFC 6052)
- RFC 3901 Authoritative Nameserver parity
- 100% precision and recall on the controlled testbed
- SSRF blocking, request tracing, API key gates, and durable job stores

---

## 🧩 Chrome Extension (Manifest V3 Side Panel)

AIORI includes a companion Manifest V3 Chrome Extension that audits any open tab in real time via the Chrome Side Panel:

1. Open Google Chrome, Brave, or Microsoft Edge and navigate to `chrome://extensions`.
2. Enable **Developer mode** (toggle in top-right corner).
3. Click **Load unpacked** and select the [`extension/`](./extension) folder in this repository.
4. Pin the **AIORI IPv6 Auditor** icon to your toolbar.
5. Click the extension icon on any webpage to open the Side Panel and initiate an instant live audit.

*Pre-packaged ZIP ready for distribution: [`extension.zip`](./extension.zip).*

---

## 👥 Hackathon Team & Regional Presentation

* **Team Code**: `A3-PS027-TC190`
* **Project**: AIORI // IPv6 Readiness & Dependency Auditor
* **Initiative**: AIORI 3.0 (NIXI & IIFON)
