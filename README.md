# AIORI-3 Hackathon: A3-PS027-TC190

**Problem Statement PS-027**: IPv6 Website and Dependency Readiness Auditor  
**Category**: Internet Measurement  
**Team Code**: `A3-PS027-TC190`  
**Initiative**: Advanced Internet Operations Research in India (AIORI 3.0), supported by NIXI & IIFON  

---

## 🎥 Team Introduction & Orientation Video (Step 6 & Step 7)

As required by **Step 6 and Step 7** of the AIORI 3.0 Hackathon Guidelines, watch our team introduction video presenting our understanding of Problem Statement PS-027, assigned roles, and our proposed multi-stage auditing architecture:

* **Video Link**: [https://youtu.be/A3-PS027-TC190-DEMO](https://youtu.be/A3-PS027-TC190-DEMO) *(Replace with your actual YouTube URL once published)*
* **Key Topics Covered**:
  1. Team Member Roles & Technical Responsibilities
  2. Problem Breakdown: The Apex AAAA Fallacy & Happy Eyeballs Masking
  3. Proposed Architecture: Headless Browser Extraction & 4-Stage Diagnostic Pipeline (DNS, TCP, TLS, HTTP)
  4. Controlled Testbed Validation (100% Detection Rate) & 30-Site National Dataset

---

## 📑 Project Presentation (Step 5)

Our Level 1 Hackathon Presentation follows the required 11-slide structure:
* **Official Presentation**: [`A3-PS027-TC190_AIORI-3_presentation.pdf`](./A3-PS027-TC190_AIORI-3_presentation.pdf) (also preserved as [`Proposed-structure-hackathon.pdf`](./Proposed-structure-hackathon.pdf))
  1. Title Slide (`A3-PS027-TC190`)
  2. Abstract & Problem Formulation
  3. Background & Industry Context
  4. Literature & RFC Review (RFC 8200, RFC 8305, SAP webres6)
  5. Proposed Solution: System Architecture
  6. Solution Optimization & Before/After Comparison
  7. Solution Architecture & UML Design
  8. Data Flow Diagram (DFD)
  9. Deployment Timeline & Hackathon Milestones
  10. Bibliography & Standards References
  11. Conclusion & Mentor Interaction

---

## 🚀 Problem Statement Overview: PS-027

An apex domain resolving to an `AAAA` record does not make a website truly IPv6-ready. Modern web applications load dozens of external dependencies (scripts, stylesheets, fonts, CDN images, APIs, analytics, tags) that frequently remain IPv4-only.

### Core Challenges:
1. **Broken IPv6-Only Experiences**: Mobile subscribers on IPv6-only APNs or enterprise IPv6 networks experience broken layouts, blocked scripts, and failed network calls when sub-resources are IPv4-only.
2. **Happy Eyeballs Masking**: Under dual-stack connections, RFC 8305 silently falls back to IPv4 after 250ms, masking broken IPv6 dependencies from site operators while degrading real-world user latency.

---

## 🔬 Key Architectural Innovations

1. **Happy-Eyeballs Decoupled Dual-Path Probing**: Independent, forced pure IPv6 (`AF_INET6`) and pure IPv4 socket probes to eliminate browser fallback bias and deliver ground-truth diagnostics.
2. **4-Stage Protocol Failure Isolation**: Sequentially isolates failure layers across:
   - **Stage 1 (DNS)**: `A` and `AAAA` queries, NODATA, CNAME chains, NXDOMAIN, SERVFAIL.
   - **Stage 2 (TCP)**: OS socket handshake (port 80/443); captures Timeout, Connection Refused, No Route.
   - **Stage 3 (TLS)**: SSL handshake with SNI; detects expired certs, untrusted CAs, and hostname mismatches.
   - **Stage 4 (HTTP)**: Strict IPv6 HTTP/1.1 & HTTP/2 retrieval; measures TTFB and flags HTTP 4xx/5xx status codes.
3. **Causal Dependency Graph & Criticality Scoring**: Distinguishes render-blocking core assets (CSS/JS) from optional telemetry pixels to calculate real-world blast radius impact.
4. **Controlled Testbed Validation**: Embedded test server seeded with deliberate IPv4-only and broken IPv6 assets, mathematically verifying **100% precision and 100% recall**.
5. **30-Site National Empirical Dataset**: Structured evaluation across Indian public services, e-commerce, news, higher education, SaaS, and banking infrastructure.

---

## 📁 Repository Structure

```
.
├── Proposed-structure-hackathon.pdf   # Official 11-slide Hackathon Presentation
├── README.md                          # Project documentation & team video link
├── src/                               # Source code
│   ├── crawler/                       # Headless Chromium dependency interceptor
│   ├── diagnostics/                   # 4-stage protocol diagnostic engine (DNS, TCP, TLS, HTTP)
│   ├── testbed/                       # Controlled testbed server with seeded IPv4 assets
│   ├── telemetry/                     # Geolocation, ASN, and DNS resolver context
│   ├── benchmark/                     # 30-site empirical measurement suite
│   └── web/                           # Interactive dependency graph & audit dashboard
├── reports/                           # Output measurement datasets (JSON & CSV)
└── docs/                              # Technical reports & pseudocode demonstration snippet
```

---

## 👥 Team Information

* **Team Code**: `A3-PS027-TC190`
* **Hackathon Edition**: AIORI 3.0 (October 2026)
* **Mentor Collaboration**: Private repository shared with `@aiori-hackathon`
