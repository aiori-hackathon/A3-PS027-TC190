# Prototype Demonstration: Pseudocode & Architectural Snippet

**Problem Statement**: PS-027 — IPv6 Website and Dependency Readiness Auditor  
**Team Code**: `A3-PS027-TC190`  
**Category**: Internet Measurement  
**Event**: AIORI 3.0 National Hackathon  

---

## 1. Mentor Demonstration Pseudocode Snippet

The following pseudocode highlights the core algorithmic innovation of our prototype: **Decoupled Dual-Path Probing** with **4-Stage Protocol Failure Isolation** and **Runtime Causal Dependency Graph Construction**.

```python
# ==============================================================================
# ALGORITHM: IPv6 Website & Dependency Readiness Auditor (PS-027)
# ==============================================================================

function AuditWebsite(target_url):
    # Step 1: Instrument Headless Browser DOM Runtime Execution
    browser_context = LaunchHeadlessChromium(bypass_cache=True, ignore_ssl=True)
    network_events = []
    
    on_network_request(req):
        if not is_data_or_blob_uri(req.url):
            network_events.append({
                "url": req.url,
                "domain": extract_fqdn(req.url),
                "resource_type": req.resource_type, # script, style, image, font, fetch
                "is_first_party": (extract_fqdn(req.url) ends_with apex_domain),
                "criticality_weight": GetCriticalityWeight(req.resource_type)
            })
            
    NavigateTo(browser_context, target_url, wait_until="domcontentloaded")
    WaitForNetworkSettle(duration=3000ms)
    Close(browser_context)

    # Step 2: Construct Directed Acyclic Dependency Graph (DAG)
    graph = BuildCausalDAG(root=apex_domain, events=network_events)
    unique_hosts = ExtractUniqueHosts(network_events)

    # Step 3: Concurrent Multi-Stage Protocol Diagnostics (DNS -> TCP -> TLS -> HTTP)
    host_diagnostics = {}
    for host in unique_hosts in parallel:
        host_diagnostics[host] = DiagnoseHostPipeline(host)

    # Step 4: Map Diagnostics, Classify Failures & Compute Scores
    total_resources = len(network_events)
    ipv6_ready_count = 0
    total_weight = 0.0
    failed_weight = 0.0
    stage_breakdown = {"DNS": 0, "TCP": 0, "TLS": 0, "HTTP": 0}

    for res in network_events:
        total_weight += res.criticality_weight
        diag = host_diagnostics[res.domain]
        
        if diag.is_ipv6_ready == True:
            ipv6_ready_count += 1
        else:
            failed_weight += res.criticality_weight
            stage_breakdown[diag.failed_stage] += 1

    # Readiness Score (%) = (IPv6-Ready Subresources / Total Subresources) * 100
    readiness_score = (ipv6_ready_count / total_resources) * 100
    # Blast Radius Impact (%) = (Weighted Failures / Total Weights) * 100
    blast_radius_impact = (failed_weight / total_weight) * 100

    return {
        "apex_domain": apex_domain,
        "readiness_score": readiness_score,
        "blast_radius_impact": blast_radius_impact,
        "stage_breakdown": stage_breakdown,
        "graph": graph,
        "telemetry": CollectClientTelemetry()
    }


# ==============================================================================
# SUB-ROUTINE: 4-Stage OSI Protocol Failure Isolation
# ==============================================================================

function DiagnoseHostPipeline(host):
    # STAGE 1: DNS Resolution
    (aaaa_records, a_records) = ResolveDNS(host)
    if length(aaaa_records) == 0:
        if length(a_records) > 0:
            return Status(code="IPV4_ONLY_DEPENDENCY", failed_stage="DNS", ready=False)
        else:
            return Status(code="GLOBAL_FAILURE", failed_stage="DNS", ready=False)
            
    target_ipv6 = aaaa_records[0]

    # STAGE 2: Direct Raw TCP Handshake (port 443 / 80)
    # Enforces AF_INET6 raw socket connect (Bypasses Happy Eyeballs fallback)
    tcp_socket = CreateSocket(AF_INET6, SOCK_STREAM, timeout=3.0s)
    tcp_result = Connect(tcp_socket, (target_ipv6, 443))
    
    if tcp_result.failed:
        Close(tcp_socket)
        return Status(code="BROKEN_IPV6_TCP", failed_stage="TCP", ready=False)

    # STAGE 3: TLS Negotiation with SNI
    tls_context = CreateTLSContext(verify=True)
    ssl_socket = WrapSocket(tls_context, tcp_socket, server_hostname=host)
    tls_result = Handshake(ssl_socket)
    
    if tls_result.failed: # Cert expired, Hostname mismatch, Untrusted CA
        Close(ssl_socket)
        return Status(code="BROKEN_IPV6_TLS", failed_stage="TLS", ready=False)

    # STAGE 4: HTTP/1.1 or HTTP/2 Retrieval & TTFB
    SendHTTPRequest(ssl_socket, method="GET", path="/", host=host)
    (http_code, ttfb_ms) = ReadHTTPResponse(ssl_socket)
    Close(ssl_socket)
    
    if http_code >= 500: # Backend gateway error over IPv6
        return Status(code="BROKEN_IPV6_HTTP", failed_stage="HTTP", ready=False)
        
    return Status(code="FULL_IPV6_READY", failed_stage=None, ready=True, ttfb=ttfb_ms)
```

---

## 2. Mathematical Scoring Formulas

### 1. IPv6 Dependency Readiness Score ($R$)
$$R = \left( \frac{N_{\text{ipv6\_ready}}}{N_{\text{total\_dependencies}}} \right) \times 100$$
* Represents the percentage of runtime resources that can be successfully fetched over pure IPv6 transport without requiring IPv4 fallback.

### 2. Critical Path Blast Radius Score ($B$)
$$B = \left( \frac{\sum_{i \in \text{Failed}} w_i}{\sum_{j \in \text{All}} w_j} \right) \times 100$$
* Where $w$ is the resource criticality weight:
  * Render-blocking Stylesheets & Document: $w = 1.0$ / $0.85$
  * Application Scripts & Core APIs: $w = 0.85$ / $0.75$
  * Fonts & Media: $w = 0.50$ / $0.30$
  * Non-critical Telemetry & Beacons: $w = 0.20$

---

## 3. Demonstration Flow for Mentors (Step 8 – 10)

1. **Launch**: Execute `python run.py`.
2. **Dashboard Overview**: Open `http://localhost:8000` to view the live dashboard.
3. **Live Audit Demo**:
   * Enter `https://digitalindia.gov.in` (demonstrating that despite being a premier national portal, ~77% of sub-resources fail on IPv6).
   * Enter `https://google.com` (demonstrating near 100% compliance).
   * Enter `https://github.com` (demonstrating apex domain lacking AAAA in Stage 1).
4. **Interactive Graph Inspection**: Click any node on the Canvas to open the slide-over drawer revealing the exact DNS, TCP RTT, TLS cipher, and HTTP status code.
5. **Controlled Testbed Ground Truth**: Switch to the **Controlled Testbed** tab to showcase **100% precision and 100% recall** against seeded IPv4-only and broken IPv6 assets.
6. **30-Site National Benchmark**: Show the cross-sectoral analytics table and download the CSV dataset.
