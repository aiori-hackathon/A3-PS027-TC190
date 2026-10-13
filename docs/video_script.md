# Team Introduction & Orientation Video Script (3 – 4 Minutes)

**Team Code**: `A3-PS027-TC190`  
**Problem Statement**: PS-027 — IPv6 Website and Dependency Readiness Auditor  
**Hackathon**: AIORI 3.0 National Hackathon (Internet Measurement Track)  
**Target Duration**: 3 minutes 30 seconds to 3 minutes 45 seconds  

---

### Speaker Distribution & Roles
* **Speaker 1 (Team Lead / Member 1)**: Problem Statement Overview, Real Browser Crawl & Dependency Graph, UI & Project Deliverables.
* **Speaker 2 (Technical Co-Lead / Member 2)**: Protocol Failure Mechanics, 4-Stage OSI Diagnostic Gauntlet, Controlled Testbed & Benchmark.

---

## 🎬 Video Recording Script

### [0:00 – 0:40] Part 1: Team & Project Introduction
*(Both speakers on screen or webcam + Slide 1)*

* **Speaker 1 [0:00 – 0:20]**:
  > *"Hello respected mentors and evaluators! We are Team **A3-PS027-TC190**, participating in the **AIORI 3.0 National Hackathon**, supported by NIXI and IIFON under the Ministry of Electronics and Information Technology.*  
  > *Our problem statement is **PS-027: IPv6 Website and Dependency Readiness Auditor** under the **Internet Measurement** category."*

* **Speaker 2 [0:20 – 0:40]**:
  > *"To solve this challenge, we have divided our technical responsibilities:*  
  > *• **[Speaker 1]** is responsible for real headless browser instrumentation, runtime network request interception, and the causal dependency graph visualizer.*  
  > *• **[Speaker 2]** leads the low-level 4-stage network diagnostic pipeline, raw socket probing over IPv6, and the controlled testbed validation suite."*

---

### [0:40 – 1:30] Part 2: The Core Problem & Motivation
*(Slide 2: Abstract & Slide 3: Background)*

* **Speaker 1 [0:40 – 1:05]**:
  > *"The premise of our project addresses a deceptive reality on today's web: **an apex domain resolving to an AAAA record does not make a website truly IPv6-ready**.*  
  > *Modern websites are complex, distributed applications. A single portal typically imports dozens of third-party stylesheets, JavaScript bundles, web fonts, CDN images, and API endpoints. If even one critical dependency remains IPv4-only, pure IPv6 users face broken page layouts, hanging scripts, and failed transactions."*

* **Speaker 2 [1:05 – 1:30]**:
  > *"This is especially crucial in India, where over 80% of mobile users are already on IPv6-enabled networks, but web dependencies have not caught up.*  
  > *Furthermore, on dual-stack devices, RFC 8305—known as **Happy Eyeballs**—masks these dependency failures by silently falling back to IPv4 after a 250-millisecond delay. This hides underlying connectivity defects from site operators while introducing unnecessary latency."*

---

### [1:30 – 2:40] Part 3: Architecture & Technical Innovations
*(Slide 5: Proposed Solution & Slide 7: System Architecture)*

* **Speaker 1 [1:30 – 2:05]**:
  > *"Existing reference tools like SAP webres6 rely on standard browser crawls where Happy Eyeballs corrupts the test data. Our auditor introduces three major technical breakthroughs:*  
  > *First, we employ **Headless Chromium via Chrome DevTools Protocol** to execute dynamic JavaScript, render CSS, and discover all asynchronous DOM dependencies along with their parent-child initiator chains.*  
  > *Second, we construct a **Causal Dependency Tree with Blast-Radius Scoring**, which accurately distinguishes render-blocking critical assets like main stylesheets from non-critical telemetry pixels."*

* **Speaker 2 [2:05 – 2:40]**:
  > *"Third, we introduce **Happy-Eyeballs Decoupled Probing**. Instead of relying on browser network fallback, our engine launches isolated, parallel socket connections strictly over pure IPv4 and pure IPv6.*  
  > *Every discovered resource is passed through an isolated **4-Stage OSI Diagnostic Gauntlet**:*  
  > *1. **DNS Stage**: Evaluating A versus AAAA records, NODATA responses, and CNAME chains.*  
  > *2. **TCP Stage**: Direct raw IPv6 socket handshakes to detect timeouts, closed ports, or routing blackholes.*  
  > *3. **TLS Stage**: Negotiating encrypted handshakes with Server Name Indication to catch certificate expiration and hostname mismatches.*  
  > *4. **HTTP Stage**: Verifying TTFB latency, HTTP status codes, and header integrity over IPv6."*

---

### [2:40 – 3:25] Part 4: Controlled Testbed & 30-Site National Benchmark
*(Slide 6: Optimization & Slide 8: Data Flow)*

* **Speaker 1 [2:40 – 3:05]**:
  > *"To ensure scientific rigor, we built a dedicated **Controlled Testbed Server**. It serves an intentionally crafted test website containing known dual-stack assets alongside deliberately seeded IPv4-only scripts, blackholed IPv6 routes, and TLS error cases.*  
  > *Our auditor runs automated assertions against this testbed to mathematically confirm **100% precision and 100% recall** before testing live sites."*

* **Speaker 2 [3:05 – 3:25]**:
  > *"Using this verified engine, we are conducting an empirical measurement campaign across **30 selected websites** covering key Indian sectors—including Government services, E-Commerce, National Media, Higher Education, Cloud SaaS, and Banking infrastructure.*  
  > *All data is exported into structured CSV and JSON datasets, complete with client network telemetry like ASN, ISP, and resolver latency."*

---

### [3:25 – 3:45] Part 5: Level 1 Milestone Completion & Closing
*(Slide 9: Timeline & Slide 11: Thank You)*

* **Speaker 1 [3:25 – 3:35]**:
  > *"We have successfully completed all Level 1 requirements: creating the official template repository, transferring ownership to `@aiori-hackathon`, uploading our 11-slide presentation deck, and recording this orientation overview."*

* **Speaker 2 [3:35 – 3:45]**:
  > *"We are thoroughly prepared for the Level 2 mentoring sessions and look forward to demonstrating our live working auditor prototype to the mentors. Thank you!"*

---

## 💡 Quick Tips for Recording
1. **Visual Setup**: Either record side-by-side using Zoom/OBS, or have one person share the presentation slides while both webcams are visible in the corner.
2. **Pacing**: Speak at a steady, natural pace. The script contains approximately 460 words, which naturally takes between **3 minutes 15 seconds and 3 minutes 45 seconds**.
3. **Upload**: Upload to YouTube as **Unlisted** or **Public**, copy the video link, and update [`README.md`](../README.md).
