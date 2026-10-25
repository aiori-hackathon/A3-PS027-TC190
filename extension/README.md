# AIORI PS-027 IPv6 Readiness Auditor (Native Chrome Extension - Manifest V3)

A complete, native in-browser Chrome extension built for **AIORI-3 PS-027** that operates as an alternative standalone client to the web dashboard (just as mobile apps complement web platforms). It runs directly inside Chrome's **Side Panel API** docked alongside any webpage the user browses, requiring **zero external tabs**.

---

## Architecture & Features

### 1. Native In-Browser Side Panel Application
- **Zero Tab-Switching Friction**: Opens natively on the right-hand side of the active browser window via `chrome.sidePanel`.
- **1-Click "Audit Active Tab"**: Auto-detects the currently active tab domain/URL and runs immediate multi-stage audits.
- **Manual Input & Preset Chips**: Test any custom URL or select presets (`india.gov.in`, `iitd.ac.in`, `amazon.in`, `github.com`, `Testbed :8888`).

### 2. Multi-Stage OSI Protocol Diagnostics
- **Stage 1: DNS Resolution**: Authoritative nameserver resolution, AAAA and A record extraction, DNS RTT.
- **Stage 2: TCP Handshake**: `AF_INET6` socket SYN/ACK to port 443, connection timing, failure isolation (`TCP_SUCCESS` vs `TCP_NO_ROUTE` / timeout).
- **Stage 3: TLS Handshake & ALPN**: TLSv1.3 negotiation, cipher suites, SNI verification, and HTTP/2 ALPN negotiation.
- **Stage 4: HTTP GET & Subresources**: Application-layer status verification and content delivery over pure IPv6.
- **Engineering Remediation Drawer**: Root-cause analysis and DNS/BGP/CDN remediation guidance per RFC 8305 and RFC 4038.

### 3. Interactive Canvas 2D DAG Topology Graph
- Dynamic visualization of the apex domain root and all first-party and third-party dependency assets.
- Color-coded protocol states:
  - **Blue**: Apex Root
  - **Green**: Pure IPv6 Compliant
  - **Red**: IPv4-Only (Missing AAAA)
  - **Amber**: Broken Route / Timeout
- **Animated Data Packet Particles**: Live particle flow along dependency edges (toggleable).
- **Interactive Controls**: Zoom (+ / - / Reset), Pan, Hover tooltips, and Click-to-Inspect node diagnostics.

### 4. 30-Site National Benchmark
- In-extension benchmark suite evaluating India's national digital infrastructure across Central Government (NIC), Higher Education (IITs), Commercial Banking, E-Commerce, and Tech Infrastructure.
- Sector performance bars and failure taxonomy distribution (Missing AAAA, Subresource Leaks, Broken Routing).
- Searchable target table with 1-click "Audit in Visualizer" routing.
- Direct CSV and JSON data export.

### 5. Controlled Testbed Suite (:8888)
- Deterministic ground-truth verification across 8 synthetic test cases on port 8888.
- Confusion matrix and metrics: 100% Precision, 100% Recall, 1.000 F1-Score.

### 6. Client Dual-Stack Telemetry
- Evaluates client machine IPv4/IPv6 address, ASN, ISP, and RFC 8305 Happy Eyeballs v2 connection preference.
- Recursive DNS resolver RTT benchmarks (Cloudflare, Google Public DNS, Quad9).

---

## Strict Minimalist Engineering Aesthetics
- Clean solid **GitHub Dark / Primer / Awwwards Standard** design (`#0d1117` and `#161b22`).
- Flat status accents: Green (`#2ea043`), Red (`#f85149`), Amber (`#d29922`), Blue (`#58a6ff`).
- **Zero gradients, zero liquid glass / backdrop filters, zero emojis.**

---

## How to Install (Load Unpacked in Chrome / Brave / Edge)

1. Open Google Chrome (or any Chromium browser).
2. Navigate to `chrome://extensions/`.
3. In the top-right corner, toggle **Developer mode** to **ON**.
4. Click the **Load unpacked** button in the top-left corner.
5. Select the `extension/` directory in this repository:
   ```bash
   /Users/apple/Aiori/extension
   ```
6. The **IPv6 Readiness Auditor** icon will appear on your browser toolbar.

---

## How to Use
1. Visit any website (e.g. `https://india.gov.in`, `https://github.com`, or `https://aiori.in`).
2. Click the extension icon in your Chrome toolbar.
3. The **Side Panel** immediately docks on the right side of your active screen.
4. Click **Audit Active Tab** or select any preset to inspect the live topology DAG and 4-stage OSI diagnostics directly inside the extension!
