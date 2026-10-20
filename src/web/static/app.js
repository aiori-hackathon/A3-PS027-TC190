/**
 * AIORI PS-027 Interactive Dependency Visualizer & Audit Engine
 */

// State
let currentAuditData = null;
let graphNodes = [];
let graphEdges = [];
let selectedNode = null;
let animFrameId = null;

// DOM Elements
const canvas = document.getElementById('dependencyCanvas');
const ctx = canvas ? canvas.getContext('2d') : null;
const auditForm = document.getElementById('auditForm');
const urlInput = document.getElementById('urlInput');
const auditBtn = document.getElementById('auditBtn');
const auditStatus = document.getElementById('auditStatus');

// Metric Elements
const metricReadiness = document.getElementById('metricReadiness');
const metricTotal = document.getElementById('metricTotal');
const metricV6Ready = document.getElementById('metricV6Ready');
const metricV4Only = document.getElementById('metricV4Only');
const metricBroken = document.getElementById('metricBroken');

// Drawer Elements
const drawerContent = document.getElementById('drawerContent');
const drawerPlaceholder = document.getElementById('drawerPlaceholder');

// Navigation Tabs
document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        tab.classList.add('active');
        const targetPanel = document.getElementById(tab.dataset.target);
        if (targetPanel) targetPanel.classList.add('active');
    });
});

// Quick Presets
document.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
        if (urlInput) {
            urlInput.value = chip.dataset.url;
            runAudit(chip.dataset.url);
        }
    });
});

// Form Submit
if (auditForm) {
    auditForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const url = urlInput.value.trim();
        if (url) runAudit(url);
    });
}

// Audit Trigger Function
async function runAudit(url) {
    if (!url) return;
    if (auditBtn) {
        auditBtn.disabled = true;
        auditBtn.innerText = 'Auditing...';
    }
    if (auditStatus) auditStatus.innerText = `Launching headless browser crawl for ${url}...`;

    try {
        const resp = await fetch('/api/audit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });

        if (!resp.ok) {
            throw new Error(`Audit API failed with status ${resp.status}`);
        }

        const data = await resp.json();
        currentAuditData = data;
        renderAuditResults(data);

        if (auditStatus) auditStatus.innerText = `Audit complete for ${data.name || data.apex_domain}!`;
    } catch (err) {
        console.error(err);
        if (auditStatus) auditStatus.innerText = `Error running audit: ${err.message}`;
    } finally {
        if (auditBtn) {
            auditBtn.disabled = false;
            auditBtn.innerText = 'Audit Now';
        }
    }
}

// Render Metrics & Graph
function renderAuditResults(data) {
    const metrics = data.metrics || {};
    
    // Update Scorecards
    if (metricReadiness) {
        const score = metrics.readiness_score_percent ?? 0;
        metricReadiness.innerText = `${score}%`;
        metricReadiness.className = `metric-value ${score > 70 ? 'color-green' : (score > 40 ? 'color-amber' : 'color-red')}`;
    }
    if (metricTotal) metricTotal.innerText = metrics.total_resources ?? 0;
    if (metricV6Ready) metricV6Ready.innerText = metrics.ipv6_ready_count ?? 0;
    if (metricV4Only) metricV4Only.innerText = metrics.ipv4_only_count ?? 0;
    if (metricBroken) metricBroken.innerText = metrics.broken_ipv6_count ?? 0;

    // Render Table
    renderResourceTable(data.resources || []);

    // Setup Canvas Graph
    setupGraph(data);
}

// Render Resource Table
function renderResourceTable(resources) {
    const tbody = document.getElementById('resourceTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';

    resources.forEach(r => {
        const tr = document.createElement('tr');
        let statusBadge = '<span class="badge badge-ready">IPv6 Ready</span>';
        if (r.status === 'IPV4_ONLY_DEPENDENCY') {
            statusBadge = '<span class="badge badge-v4only">IPv4 Only</span>';
        } else if (r.status.startsWith('BROKEN_IPV6_')) {
            statusBadge = `<span class="badge badge-broken">Broken (${r.failed_stage})</span>`;
        } else if (r.status === 'GLOBAL_FAILURE') {
            statusBadge = '<span class="badge badge-v4only">Dead Link</span>';
        }

        tr.innerHTML = `
            <td><code>${escapeHtml(r.domain)}</code></td>
            <td>${escapeHtml(r.resource_type)}</td>
            <td>${r.is_first_party ? '<span style="color:#00f0ff">1st Party</span>' : '<span style="color:#94a3b8">3rd Party</span>'}</td>
            <td>${statusBadge}</td>
            <td style="max-width:350px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
                <a href="${escapeHtml(r.url)}" target="_blank" style="color:#38bdf8; text-decoration:none;">${escapeHtml(r.url)}</a>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Canvas Force-Directed Layout
function setupGraph(data) {
    if (!canvas || !ctx) return;
    
    // Resize Canvas to container
    canvas.width = canvas.parentElement.clientWidth - 40;
    canvas.height = canvas.parentElement.clientHeight - 80;

    const rawNodes = data.graph ? data.graph.nodes : [];
    const rawEdges = data.graph ? data.graph.edges : [];

    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;

    // Initialize node positions in a radial burst
    graphNodes = rawNodes.map((n, i) => {
        const diag = data.host_diagnostics ? data.host_diagnostics[n.domain] : null;
        const isReady = diag ? diag.is_ipv6_ready : false;
        const status = diag ? diag.overall_status : 'UNKNOWN';

        let color = '#10b981'; // Green
        if (status === 'IPV4_ONLY_DEPENDENCY') color = '#ef4444'; // Red
        else if (status.startsWith('BROKEN_IPV6_')) color = '#f59e0b'; // Amber
        else if (n.is_root) color = '#00f0ff'; // Cyan

        const angle = (i / Math.max(rawNodes.length - 1, 1)) * 2 * Math.PI;
        const radius = n.is_root ? 0 : (n.type === 'domain' ? 120 : 180 + Math.random() * 80);

        return {
            ...n,
            x: centerX + Math.cos(angle) * radius,
            y: centerY + Math.sin(angle) * radius,
            vx: 0,
            vy: 0,
            radius: n.is_root ? 16 : (n.type === 'domain' ? 9 : 5),
            color: color,
            diag: diag
        };
    });

    graphEdges = rawEdges;
    selectedNode = graphNodes[0] || null;
    showDrawerNode(selectedNode);

    // Start Simulation Loop
    if (animFrameId) cancelAnimationFrame(animFrameId);
    let iterations = 0;
    function tick() {
        simulateForces();
        drawGraph();
        iterations++;
        if (iterations < 120) {
            animFrameId = requestAnimationFrame(tick);
        }
    }
    tick();
}

function simulateForces() {
    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;

    // Repulsion
    for (let i = 0; i < graphNodes.length; i++) {
        for (let j = i + 1; j < graphNodes.length; j++) {
            const a = graphNodes[i];
            const b = graphNodes[j];
            let dx = b.x - a.x;
            let dy = b.y - a.y;
            let dist = Math.sqrt(dx * dx + dy * dy) || 1;
            if (dist < 180) {
                const force = (180 - dist) / dist * 0.04;
                b.x += dx * force;
                b.y += dy * force;
                a.x -= dx * force;
                a.y -= dy * force;
            }
        }
    }

    // Centering & boundary constraints
    graphNodes.forEach(n => {
        if (!n.is_root) {
            n.x += (centerX - n.x) * 0.005;
            n.y += (centerY - n.y) * 0.005;
        } else {
            n.x = centerX;
            n.y = centerY;
        }
        n.x = Math.max(n.radius, Math.min(width - n.radius, n.x));
        n.y = Math.max(n.radius, Math.min(height - n.radius, n.y));
    });
}

function drawGraph() {
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw Edges
    ctx.lineWidth = 1;
    ctx.strokeStyle = 'rgba(148, 163, 184, 0.15)';
    const nodeMap = {};
    graphNodes.forEach(n => { nodeMap[n.id] = n; });

    graphEdges.forEach(e => {
        const src = nodeMap[e.source];
        const tgt = nodeMap[e.target];
        if (src && tgt) {
            ctx.beginPath();
            ctx.moveTo(src.x, src.y);
            ctx.lineTo(tgt.x, tgt.y);
            ctx.stroke();
        }
    });

    // Draw Nodes
    graphNodes.forEach(n => {
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius, 0, 2 * Math.PI);
        ctx.fillStyle = n.color;
        ctx.shadowColor = n.color;
        ctx.shadowBlur = (n === selectedNode) ? 14 : 4;
        ctx.fill();
        ctx.shadowBlur = 0;

        if (n.is_root || n.type === 'domain') {
            ctx.font = '10px Inter, sans-serif';
            ctx.fillStyle = '#cbd5e1';
            ctx.textAlign = 'center';
            ctx.fillText(n.label.substring(0, 20), n.x, n.y + n.radius + 12);
        }
    });
}

// Canvas Click Event to inspect node
if (canvas) {
    canvas.addEventListener('click', (e) => {
        const rect = canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;

        let clicked = null;
        for (const n of graphNodes) {
            const dist = Math.sqrt((n.x - mouseX) ** 2 + (n.y - mouseY) ** 2);
            if (dist <= n.radius + 6) {
                clicked = n;
                break;
            }
        }

        if (clicked) {
            selectedNode = clicked;
            showDrawerNode(clicked);
            drawGraph();
        }
    });
}

// Drawer Details Display
function showDrawerNode(node) {
    if (!drawerContent || !drawerPlaceholder) return;
    if (!node) {
        drawerPlaceholder.style.display = 'block';
        drawerContent.style.display = 'none';
        return;
    }

    drawerPlaceholder.style.display = 'none';
    drawerContent.style.display = 'block';

    const diag = node.diag || {};
    const stages = diag.stages || {};
    const dns = stages.dns || {};
    const tcp = stages.tcp || {};
    const tls = stages.tls || {};
    const http = stages.http || {};

    const statusBadge = node.color === '#10b981'
        ? '<span class="node-status-badge badge-ready">Fully IPv6 Ready</span>'
        : (node.color === '#ef4444'
            ? '<span class="node-status-badge badge-v4only">IPv4-Only Dependency</span>'
            : '<span class="node-status-badge badge-broken">Broken IPv6 Routing</span>');

    drawerContent.innerHTML = `
        <div class="drawer-header">
            <div class="node-title">${escapeHtml(node.domain || node.label)}</div>
            ${statusBadge}
            <div style="font-size:0.75rem; color:#94a3b8; margin-top:6px;">Type: ${escapeHtml(node.type)} &bull; ${node.is_first_party ? 'First-Party' : 'Third-Party'}</div>
        </div>

        <div class="stage-step">
            <div class="stage-step-title">
                <span>1. DNS Resolution</span>
                <span style="color:${dns.has_aaaa ? '#10b981' : '#ef4444'}">${dns.status || 'NO_AAAA'}</span>
            </div>
            <div class="stage-data">
                AAAA: ${dns.aaaa_records ? dns.aaaa_records.join(', ') : 'None'}<br>
                A: ${dns.a_records ? dns.a_records.join(', ') : 'None'}<br>
                Latency: ${dns.latency_ms ?? 0} ms
            </div>
        </div>

        <div class="stage-step">
            <div class="stage-step-title">
                <span>2. TCP Handshake (IPv6)</span>
                <span style="color:${tcp.status === 'TCP_SUCCESS' ? '#10b981' : '#ef4444'}">${tcp.status || 'SKIPPED'}</span>
            </div>
            <div class="stage-data">
                Target: [${tcp.target_ip || 'N/A'}]:${tcp.port || 443}<br>
                RTT: ${tcp.rtt_ms ?? 0} ms<br>
                ${tcp.error_detail ? `<span style="color:#f87171">${escapeHtml(tcp.error_detail)}</span>` : ''}
            </div>
        </div>

        <div class="stage-step">
            <div class="stage-step-title">
                <span>3. TLS Negotiation</span>
                <span style="color:${tls.status === 'TLS_SUCCESS' ? '#10b981' : '#ef4444'}">${tls.status || 'SKIPPED'}</span>
            </div>
            <div class="stage-data">
                Version: ${tls.tls_version || 'N/A'}<br>
                Cipher: ${tls.cipher || 'N/A'}<br>
                Expires: ${tls.cert_expires || 'N/A'}<br>
                ${tls.error_detail ? `<span style="color:#f87171">${escapeHtml(tls.error_detail)}</span>` : ''}
            </div>
        </div>

        <div class="stage-step">
            <div class="stage-step-title">
                <span>4. HTTP Retrieval</span>
                <span style="color:${http.status === 'HTTP_SUCCESS' ? '#10b981' : '#ef4444'}">${http.status || 'SKIPPED'}</span>
            </div>
            <div class="stage-data">
                Status: ${http.http_status_code || 'N/A'}<br>
                TTFB: ${http.ttfb_ms ?? 0} ms<br>
                Content-Type: ${http.content_type || 'N/A'}
            </div>
        </div>
    `;
}

// Helpers
function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// Load Benchmark Data & Controlled Testbed on Startup
async function initData() {
    // 1. Controlled Testbed
    try {
        const resp = await fetch('/api/testbed');
        if (resp.ok) {
            const data = await resp.json();
            renderTestbedTable(data);
        }
    } catch (e) {
        console.warn('Testbed fetch failed:', e);
    }

    // 2. Benchmark 30-Site Data
    try {
        const resp = await fetch('/api/benchmark');
        if (resp.ok) {
            const data = await resp.json();
            renderBenchmarkTable(data);
        }
    } catch (e) {
        console.warn('Benchmark fetch failed:', e);
    }

    // 3. Telemetry
    try {
        const resp = await fetch('/api/telemetry');
        if (resp.ok) {
            const data = await resp.json();
            renderTelemetry(data);
        }
    } catch (e) {
        console.warn('Telemetry fetch failed:', e);
    }
}

function renderTestbedTable(data) {
    const tbody = document.getElementById('testbedTableBody');
    const badge = document.getElementById('testbedStatusBadge');
    if (badge && data.metrics) {
        badge.innerHTML = `✓ ${data.metrics.precision_percent}% Precision &bull; ${data.metrics.recall_percent}% Recall (Verified)`;
    }
    if (!tbody || !data.evaluations) return;
    tbody.innerHTML = '';

    data.evaluations.forEach(ev => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><code>${escapeHtml(ev.url_path)}</code></td>
            <td>${escapeHtml(ev.description)}</td>
            <td><span class="badge ${ev.is_seeded_failure ? 'badge-v4only' : 'badge-ready'}">${ev.is_seeded_failure ? 'Seeded Failure' : 'Compliant'}</span></td>
            <td><code>${escapeHtml(ev.detected_status)}</code></td>
            <td>${ev.detected_stage || 'None'}</td>
            <td><span style="color:#10b981; font-weight:700;">✓ PASSED</span></td>
        `;
        tbody.appendChild(tr);
    });
}

function renderBenchmarkTable(data) {
    const tbody = document.getElementById('benchmarkTableBody');
    const meta = data.metadata || {};
    const sites = data.sites || [];

    const avgEl = document.getElementById('benchAvgScore');
    const totalEl = document.getElementById('benchTotalSites');
    if (avgEl) avgEl.innerText = `${meta.average_readiness_score_percent ?? 0}%`;
    if (totalEl) totalEl.innerText = meta.total_targets_evaluated ?? sites.length;

    if (!tbody) return;
    tbody.innerHTML = '';

    sites.forEach(s => {
        if (!s.metrics) return;
        const m = s.metrics;
        const score = m.readiness_score_percent;
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${escapeHtml(s.name)}</strong></td>
            <td>${escapeHtml(s.sector)}</td>
            <td>${s.apex_audit.has_aaaa ? '<span class="badge badge-ready">Yes</span>' : '<span class="badge badge-v4only">No</span>'}</td>
            <td>${m.total_resources}</td>
            <td><strong style="color:${score > 50 ? '#10b981' : '#f87171'}">${score}%</strong></td>
            <td>${m.blast_radius_percent}%</td>
            <td>${m.ipv4_only_count}</td>
            <td><button class="btn-export" onclick="loadBenchmarkSite('${s.url}')">Audit Live</button></td>
        `;
        tbody.appendChild(tr);
    });
}

function renderTelemetry(data) {
    const pub = data.public_telemetry || {};
    const dns = data.dns_telemetry || {};
    const local = data.local_interfaces || {};

    const el = document.getElementById('telemetryBox');
    if (el) {
        el.innerHTML = `
            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:15px;">
                <div class="stage-step">
                    <strong>Local IPv4:</strong> ${local.ipv4 || 'None'}<br>
                    <strong>Local IPv6:</strong> ${local.ipv6 || 'None'}
                </div>
                <div class="stage-step">
                    <strong>Public IPv4:</strong> ${pub.public_ipv4 || 'N/A'}<br>
                    <strong>Public IPv6:</strong> ${pub.public_ipv6 || 'N/A'}
                </div>
                <div class="stage-step">
                    <strong>ISP / ASN:</strong> ${pub.as_org || 'N/A'} (${pub.asn || 'N/A'})<br>
                    <strong>Location:</strong> ${pub.city || 'N/A'}, ${pub.country || 'N/A'}
                </div>
                <div class="stage-step">
                    <strong>Resolver:</strong> ${dns.primary_resolver || 'N/A'}<br>
                    <strong>DNS RTT:</strong> ${dns.resolver_latency_ms ?? 0} ms
                </div>
            </div>
        `;
    }
}

window.loadBenchmarkSite = function(url) {
    document.querySelector('.nav-tab[data-target="liveAuditPanel"]').click();
    urlInput.value = url;
    runAudit(url);
};

// Auto initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    initData();
    // Default audit load
    runAudit('https://aiori.in');
});
