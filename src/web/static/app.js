/**
 * AIORI PS-027 IPv6 Website & Dependency Readiness Auditor
 * Clean Minimalist Client Engine (GitHub / Awwwards Standard)
 * Zero gradients, zero liquid glass, zero emojis.
 */

// Global State
let currentAuditData = null;
let graphNodes = [];
let graphEdges = [];
let graphParticles = [];
let selectedNode = null;
let hoveredNode = null;
let draggedNode = null;
let activeFilter = 'all';
let particlesEnabled = true;
let animFrameId = null;

// Camera Transform State
let camera = {
    x: 0,
    y: 0,
    zoom: 1,
    isDragging: false,
    dragStartX: 0,
    dragStartY: 0
};

// DOM Elements
const canvas = document.getElementById('dependencyCanvas');
const ctx = canvas ? canvas.getContext('2d') : null;
const tooltip = document.getElementById('canvasTooltip');
const auditForm = document.getElementById('auditForm');
const urlInput = document.getElementById('urlInput');
const auditBtn = document.getElementById('auditBtn');
const auditStatusPill = document.getElementById('auditStatusPill');

// Scorecard Elements
const metricReadiness = document.getElementById('metricReadiness');
const metricTotal = document.getElementById('metricTotal');
const metricV6Ready = document.getElementById('metricV6Ready');
const metricV4Only = document.getElementById('metricV4Only');
const metricBroken = document.getElementById('metricBroken');

// Drawer Elements
const drawerContent = document.getElementById('drawerContent');
const drawerPlaceholder = document.getElementById('drawerPlaceholder');
const inspectorDomainBadge = document.getElementById('inspectorDomainBadge');

// Terminal Elements
const terminalStream = document.getElementById('terminalStream');
let terminalLogs = [];
let activeTerminalStage = 'ALL';

// ==========================================
// 1. INITIALIZATION & NAVIGATION
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initCanvasEvents();
    initPresetChips();
    initTerminalActions();
    initTestbedActions();
    loadTelemetryContext();
    loadBenchmarkData();
    loadTestbedVerification();

    // Auto-run initial audit on default target
    if (urlInput && urlInput.value) {
        runAudit(urlInput.value);
    }
});

function initNavigation() {
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.nav-tab').forEach(t => {
                t.classList.remove('active');
                t.setAttribute('aria-selected', 'false');
            });
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));

            tab.classList.add('active');
            tab.setAttribute('aria-selected', 'true');
            const target = document.getElementById(tab.dataset.target);
            if (target) target.classList.add('active');

            if (tab.dataset.target === 'liveAuditPanel') {
                resizeCanvas();
            }
        });
    });

    // Form submit
    if (auditForm) {
        auditForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const url = urlInput.value.trim();
            if (url) runAudit(url);
        });
    }

    // Resource Table Search Filter
    const resourceSearch = document.getElementById('resourceFilterInput');
    if (resourceSearch) {
        resourceSearch.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('#resourceTableBody tr');
            rows.forEach(r => {
                const text = r.textContent.toLowerCase();
                r.style.display = text.includes(query) ? '' : 'none';
            });
        });
    }
}

function initPresetChips() {
    document.querySelectorAll('.chip').forEach(chip => {
        chip.addEventListener('click', () => {
            if (urlInput) {
                urlInput.value = chip.dataset.url;
                runAudit(chip.dataset.url);
            }
        });
    });
}

// ==========================================
// 2. LIVE AUDIT EXECUTION & TERMINAL LOGGING
// ==========================================

async function runAudit(url) {
    if (!url) return;
    if (auditBtn) {
        auditBtn.disabled = true;
        auditBtn.innerHTML = `<span>Auditing...</span>`;
    }
    if (auditStatusPill) {
        auditStatusPill.className = 'status-pill status-loading';
        auditStatusPill.innerText = 'Crawl in Progress';
    }

    logToTerminal('SYSTEM', `Initiating headless Chromium dependency extraction for ${url}...`);

    try {
        const resp = await fetch('/api/audit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });

        if (!resp.ok) {
            throw new Error(`Audit HTTP ${resp.status}: ${resp.statusText}`);
        }

        const data = await resp.json();
        currentAuditData = data;
        renderAuditResults(data);

        logToTerminal('SYSTEM', `Crawl complete. Discovered ${data.metrics?.total_resources || 0} sub-resources across ${data.metrics?.total_domains || 0} host domains.`);
        
        // Log individual host probe summaries to terminal
        if (data.host_diagnostics) {
            const entries = Object.entries(data.host_diagnostics);
            const maxLog = 100;
            entries.slice(0, maxLog).forEach(([domain, diag]) => {
                const stage = diag.is_ipv6_ready ? 'HTTP' : (diag.failed_at_stage || 'DNS');
                const statusStr = diag.is_ipv6_ready ? 'IPv6 READY' : `${diag.overall_status}`;
                const pass = diag.is_ipv6_ready;
                const rttVal = diag.stages?.http?.ttfb_ms ?? diag.stages?.tcp?.rtt_ms ?? null;
                const rttDisplay = rttVal !== null ? `${rttVal}ms` : '--';
                logToTerminal(stage, `${domain} -> ${statusStr} (IPv6: ${rttDisplay})`, pass);
            });
            if (entries.length > maxLog) {
                logToTerminal('SYSTEM', `+${entries.length - maxLog} more hosts discovered and diagnosed.`, true);
            }
        }

        if (auditStatusPill) {
            auditStatusPill.className = 'status-pill status-ready';
            auditStatusPill.innerText = `Audit Complete | ${data.metrics?.readiness_score_percent || 0}% Ready`;
        }
    } catch (err) {
        console.error(err);
        logToTerminal('ERROR', `Audit failed: ${err.message}`, false);
        if (auditStatusPill) {
            auditStatusPill.className = 'status-pill status-error';
            auditStatusPill.innerText = 'Audit Failed';
        }
    } finally {
        if (auditBtn) {
            auditBtn.disabled = false;
            auditBtn.innerHTML = `<span>Audit Target</span><span class="btn-kbd font-mono">Enter</span>`;
        }
    }
}

function renderAuditResults(data) {
    const metrics = data.metrics || {};
    const score = metrics.readiness_score_percent ?? 0;

    // Metric Scorecards
    if (metricReadiness) {
        metricReadiness.innerText = `${score}%`;
        metricReadiness.className = `metric-value font-mono ${score >= 75 ? 'text-green' : (score >= 40 ? 'text-amber' : 'text-red')}`;
    }

    if (metricTotal) metricTotal.innerText = metrics.total_resources ?? 0;
    if (metricV6Ready) metricV6Ready.innerText = metrics.ipv6_ready_count ?? 0;
    if (metricV4Only) metricV4Only.innerText = metrics.ipv4_only_count ?? 0;
    if (metricBroken) metricBroken.innerText = metrics.broken_ipv6_count ?? 0;

    const metricNsAudit = document.getElementById('metricNsAudit');
    if (metricNsAudit) {
        const ns = metrics.ns_audit;
        if (ns && ns.total_nameservers > 0) {
            metricNsAudit.innerText = `${ns.ipv6_nameservers_count}/${ns.total_nameservers}`;
            metricNsAudit.className = `metric-value font-mono ${ns.rfc3901_compliant ? 'text-green' : (ns.ipv6_nameservers_count > 0 ? 'text-amber' : 'text-red')}`;
        } else {
            metricNsAudit.innerText = '--';
            metricNsAudit.className = 'metric-value font-mono text-blue';
        }
    }

    const metricIpv4Lit = document.getElementById('metricIpv4Lit');
    if (metricIpv4Lit) {
        const v4Lits = metrics.ipv4_literals_count || 0;
        metricIpv4Lit.innerText = v4Lits;
        metricIpv4Lit.className = `metric-value font-mono ${v4Lits > 0 ? 'text-red' : 'text-green'}`;
    }

    // Render Table
    renderResourceTable(data.resources || []);

    // Setup Canvas Topology
    setupTopologyGraph(data);
}

function renderResourceTable(resources) {
    const tbody = document.getElementById('resourceTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';

    if (resources.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="table-empty font-mono">No sub-resources discovered on target.</td></tr>`;
        return;
    }

    resources.forEach(r => {
        const tr = document.createElement('tr');
        let statusBadge = '<span class="badge badge-ready">IPv6 Ready</span>';
        if (r.is_ipv4_literal) {
            statusBadge = '<span class="badge badge-broken" title="Raw IPv4 literal breaks on IPv6 networks (RFC 6052)">IPv4 Literal (RFC 6052)</span>';
        } else if (r.status === 'IPV4_ONLY_DEPENDENCY') {
            statusBadge = '<span class="badge badge-v4only">IPv4 Only (No AAAA)</span>';
        } else if (r.status.startsWith('BROKEN_IPV6_')) {
            statusBadge = `<span class="badge badge-broken">Broken (${r.failed_stage})</span>`;
        } else if (r.status === 'GLOBAL_FAILURE') {
            statusBadge = '<span class="badge badge-v4only">Dead Link</span>';
        }

        tr.innerHTML = `
            <td><code class="font-mono text-blue">${escapeHtml(r.domain)}</code></td>
            <td><span style="font-size:0.75rem; color:var(--text-muted);">${escapeHtml(r.resource_type)}</span></td>
            <td>${r.is_first_party ? '<span class="text-blue font-mono" style="font-size:0.72rem;">1st Party</span>' : '<span style="font-size:0.72rem; color:var(--text-muted);">3rd Party</span>'}</td>
            <td>${statusBadge}</td>
            <td style="max-width:320px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
                <a href="${escapeHtml(r.url)}" target="_blank" rel="noopener noreferrer" style="color:var(--text-secondary); text-decoration:none; font-family:var(--font-mono); font-size:0.74rem;">${escapeHtml(r.url)}</a>
            </td>
        `;

        tr.addEventListener('click', () => {
            const matchingNode = graphNodes.find(n => n.domain === r.domain);
            if (matchingNode) {
                selectNode(matchingNode);
            }
        });
        tbody.appendChild(tr);
    });
}

// ==========================================
// 3. CANVAS 2D TOPOLOGY & PARTICLE ENGINE
// ==========================================

function setupTopologyGraph(data) {
    if (!canvas || !ctx) return;
    resizeCanvas();

    const rawNodes = data.graph ? data.graph.nodes : [];
    const rawEdges = data.graph ? data.graph.edges : [];

    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;

    // Reset Camera
    camera.x = 0;
    camera.y = 0;
    camera.zoom = 1;

    // Build Node objects with solid flat colors (No gradients, no glass)
    graphNodes = rawNodes.map((n, i) => {
        const diag = data.host_diagnostics ? data.host_diagnostics[n.domain] : null;
        const status = diag ? diag.overall_status : 'UNKNOWN';

        let color = '#2ea043'; // GitHub Green
        let statusCategory = 'ready';

        if (status === 'IPV4_ONLY_DEPENDENCY') {
            color = '#f85149'; // GitHub Red
            statusCategory = 'v4only';
        } else if (status.startsWith('BROKEN_IPV6_') || status === 'GLOBAL_FAILURE') {
            color = '#d29922'; // GitHub Amber
            statusCategory = 'broken';
        } else if (n.is_root) {
            color = '#58a6ff'; // GitHub Blue
            statusCategory = 'root';
        }

        const angle = (i / Math.max(rawNodes.length - 1, 1)) * 2 * Math.PI;
        const radius = n.is_root ? 14 : (n.type === 'domain' ? 8 : 4);

        return {
            ...n,
            x: centerX + Math.cos(angle) * radius,
            y: centerY + Math.sin(angle) * radius,
            vx: 0,
            vy: 0,
            radius: n.is_root ? 14 : (n.type === 'domain' ? 8 : 5),
            color: color,
            diag: diag,
            statusCategory: statusCategory,
            isFirstParty: n.is_first_party ?? false
        };
    });

    graphEdges = rawEdges;

    // Build Directed Packet Particles along edges
    graphParticles = [];
    const nodeMap = {};
    graphNodes.forEach(n => { nodeMap[n.id] = n; });

    graphEdges.forEach(e => {
        const src = nodeMap[e.source];
        const tgt = nodeMap[e.target];
        if (src && tgt) {
            const particleCount = 2;
            for (let p = 0; p < particleCount; p++) {
                graphParticles.push({
                    source: src,
                    target: tgt,
                    progress: Math.random(),
                    speed: 0.003 + Math.random() * 0.003,
                    color: tgt.color,
                    isBroken: tgt.statusCategory === 'v4only' || tgt.statusCategory === 'broken'
                });
            }
        }
    });

    // Auto-select root or first node
    selectedNode = graphNodes[0] || null;
    showDrawerNode(selectedNode);

    // Run Physics Simulation Loop
    if (animFrameId) cancelAnimationFrame(animFrameId);
    let stepCount = 0;

    function renderLoop() {
        if (stepCount < 180 || draggedNode) {
            simulateGraphPhysics();
            stepCount++;
        }
        updateParticles();
        drawTopologyCanvas();
        animFrameId = requestAnimationFrame(renderLoop);
    }
    renderLoop();
}

function simulateGraphPhysics() {
    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;

    // Node Repulsion Force
    const len = graphNodes.length;
    for (let i = 0; i < len; i++) {
        for (let j = i + 1; j < len; j++) {
            const a = graphNodes[i];
            const b = graphNodes[j];
            let dx = b.x - a.x;
            let dy = b.y - a.y;
            let dist = Math.sqrt(dx * dx + dy * dy) || 1;
            if (dist < 150) {
                const force = (150 - dist) / dist * 0.05;
                b.x += dx * force;
                b.y += dy * force;
                a.x -= dx * force;
                a.y -= dy * force;
            }
        }
    }

    // Centering & bounds
    graphNodes.forEach(n => {
        if (n === draggedNode) return;
        if (!n.is_root) {
            n.x += (centerX - n.x) * 0.006;
            n.y += (centerY - n.y) * 0.006;
        } else {
            n.x = centerX;
            n.y = centerY;
        }
        n.x = Math.max(n.radius + 10, Math.min(width - n.radius - 10, n.x));
        n.y = Math.max(n.radius + 10, Math.min(height - n.radius - 10, n.y));
    });
}

function updateParticles() {
    if (!particlesEnabled) return;
    graphParticles.forEach(p => {
        p.progress += p.speed;
        if (p.progress >= 1) {
            p.progress = 0;
        }
    });
}

function drawTopologyCanvas() {
    if (!ctx || !canvas) return;
    // Solid background (no gradients)
    ctx.fillStyle = '#0d1117';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.save();
    // Apply Camera Transform
    ctx.translate(canvas.width / 2 + camera.x, canvas.height / 2 + camera.y);
    ctx.scale(camera.zoom, camera.zoom);
    ctx.translate(-canvas.width / 2, -canvas.height / 2);

    const nodeMap = {};
    graphNodes.forEach(n => { nodeMap[n.id] = n; });

    // 1. Draw Edges (Solid 1px lines)
    graphEdges.forEach(e => {
        const src = nodeMap[e.source];
        const tgt = nodeMap[e.target];
        if (!src || !tgt) return;

        const isFilteredOut = isNodeFiltered(src) || isNodeFiltered(tgt);
        
        if (hoveredNode && (src === hoveredNode || tgt === hoveredNode)) {
            ctx.strokeStyle = '#58a6ff';
            ctx.lineWidth = 1.5;
        } else {
            ctx.strokeStyle = isFilteredOut ? '#161b22' : '#30363d';
            ctx.lineWidth = 1;
        }

        ctx.beginPath();
        ctx.moveTo(src.x, src.y);
        ctx.lineTo(tgt.x, tgt.y);
        ctx.stroke();
    });

    // 2. Draw Packet Flow Particles (Solid micro-dots)
    if (particlesEnabled) {
        graphParticles.forEach(p => {
            if (isNodeFiltered(p.source) || isNodeFiltered(p.target)) return;
            const px = p.source.x + (p.target.x - p.source.x) * p.progress;
            const py = p.source.y + (p.target.y - p.source.y) * p.progress;

            ctx.beginPath();
            ctx.arc(px, py, 2, 0, 2 * Math.PI);
            ctx.fillStyle = p.isBroken ? '#f85149' : '#2ea043';
            ctx.fill();
        });
    }

    // 3. Draw Nodes (Solid, flat circles with 1px border)
    graphNodes.forEach(n => {
        const filtered = isNodeFiltered(n);
        const isHovered = n === hoveredNode;
        const isSelected = n === selectedNode;

        ctx.save();
        ctx.globalAlpha = filtered ? 0.2 : 1.0;

        // Selection / Hover Indicator Ring
        if (isSelected || isHovered) {
            ctx.beginPath();
            ctx.arc(n.x, n.y, n.radius + 4, 0, 2 * Math.PI);
            ctx.strokeStyle = '#58a6ff';
            ctx.lineWidth = 1.5;
            ctx.stroke();
        }

        // Concentric ring for Root
        if (n.is_root) {
            ctx.beginPath();
            ctx.arc(n.x, n.y, n.radius + 3, 0, 2 * Math.PI);
            ctx.strokeStyle = '#30363d';
            ctx.lineWidth = 1;
            ctx.stroke();
        }

        // Node Solid Circle
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius, 0, 2 * Math.PI);
        ctx.fillStyle = n.color;
        ctx.fill();

        // 1px Solid Neutral Border
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 1;
        ctx.stroke();

        // Node Label
        if (n.is_root || n.type === 'domain') {
            ctx.font = '500 11px Inter, -apple-system, sans-serif';
            ctx.fillStyle = isSelected ? '#f0f6fc' : '#8b949e';
            ctx.textAlign = 'center';
            ctx.fillText(truncate(n.domain || n.label || '', 18), n.x, n.y + n.radius + 14);
        }

        ctx.restore();
    });

    ctx.restore();
}

function isNodeFiltered(node) {
    if (activeFilter === 'all') return false;
    if (activeFilter === 'v4only') return node.statusCategory !== 'v4only';
    if (activeFilter === 'broken') return node.statusCategory !== 'broken';
    if (activeFilter === '3rdparty') return node.isFirstParty || node.is_root;
    return false;
}

// ==========================================
// 4. CANVAS INTERACTION (ZOOM, PAN, HOVER, DRAG)
// ==========================================

function initCanvasEvents() {
    if (!canvas) return;
    window.addEventListener('resize', resizeCanvas);

    // Zoom buttons
    document.getElementById('btnZoomIn')?.addEventListener('click', () => zoomCamera(1.2));
    document.getElementById('btnZoomOut')?.addEventListener('click', () => zoomCamera(0.8));
    document.getElementById('btnResetView')?.addEventListener('click', resetCamera);
    
    // Toggle Particles
    const toggleBtn = document.getElementById('btnToggleParticles');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            particlesEnabled = !particlesEnabled;
            toggleBtn.classList.toggle('active', particlesEnabled);
        });
    }

    // Filter Buttons
    document.querySelectorAll('.filter-pill[data-filter]').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-pill[data-filter]').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            activeFilter = btn.dataset.filter;
        });
    });

    // Mouse Wheel Zoom
    canvas.addEventListener('wheel', (e) => {
        e.preventDefault();
        const factor = e.deltaY < 0 ? 1.08 : 0.92;
        zoomCamera(factor);
    }, { passive: false });

    // Mouse Down (Start Pan or Drag Node)
    canvas.addEventListener('mousedown', (e) => {
        const mouse = getCanvasMousePos(e);
        const hitNode = findNodeAt(mouse.x, mouse.y);

        if (hitNode) {
            draggedNode = hitNode;
            selectNode(hitNode);
        } else {
            camera.isDragging = true;
            camera.dragStartX = e.clientX - camera.x;
            camera.dragStartY = e.clientY - camera.y;
        }
    });

    // Mouse Move (Pan Canvas, Drag Node, or Hover)
    canvas.addEventListener('mousemove', (e) => {
        if (camera.isDragging) {
            camera.x = e.clientX - camera.dragStartX;
            camera.y = e.clientY - camera.dragStartY;
            return;
        }

        const mouse = getCanvasMousePos(e);

        if (draggedNode) {
            draggedNode.x = mouse.x;
            draggedNode.y = mouse.y;
            return;
        }

        const hitNode = findNodeAt(mouse.x, mouse.y);
        hoveredNode = hitNode;
        canvas.style.cursor = hitNode ? 'pointer' : 'grab';

        // Floating Tooltip
        if (hitNode && tooltip) {
            const rect = canvas.getBoundingClientRect();
            tooltip.style.display = 'block';
            tooltip.style.left = `${e.clientX - rect.left + 14}px`;
            tooltip.style.top = `${e.clientY - rect.top + 14}px`;
            
            const tcpRtt = hitNode.diag?.stages?.tcp?.rtt_ms;
            const rttStr = (tcpRtt !== undefined && tcpRtt !== null) ? `${tcpRtt}ms` : '--';
            tooltip.innerHTML = `
                <div><strong>${escapeHtml(hitNode.domain || hitNode.label || '')}</strong></div>
                <div style="color:var(--text-muted); font-size:0.68rem; margin-top:2px;">
                    Status: <span style="color:${hitNode.color}">${hitNode.statusCategory.toUpperCase()}</span> | RTT: ${rttStr}
                </div>
            `;
        } else if (tooltip) {
            tooltip.style.display = 'none';
        }
    });

    // Mouse Up / Leave
    const endInteraction = () => {
        camera.isDragging = false;
        draggedNode = null;
        if (tooltip) tooltip.style.display = 'none';
    };
    canvas.addEventListener('mouseup', endInteraction);
    canvas.addEventListener('mouseleave', endInteraction);
}

function getCanvasMousePos(e) {
    const rect = canvas.getBoundingClientRect();
    const clientX = e.clientX - rect.left;
    const clientY = e.clientY - rect.top;

    // Invert Camera Transform
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    const worldX = (clientX - cx - camera.x) / camera.zoom + cx;
    const worldY = (clientY - cy - camera.y) / camera.zoom + cy;
    return { x: worldX, y: worldY };
}

function findNodeAt(x, y) {
    for (let i = graphNodes.length - 1; i >= 0; i--) {
        const n = graphNodes[i];
        if (isNodeFiltered(n)) continue;
        const dx = x - n.x;
        const dy = y - n.y;
        if (dx * dx + dy * dy <= (n.radius + 6) * (n.radius + 6)) {
            return n;
        }
    }
    return null;
}

function zoomCamera(factor) {
    camera.zoom = Math.max(0.4, Math.min(3.0, camera.zoom * factor));
}

function resetCamera() {
    camera.x = 0;
    camera.y = 0;
    camera.zoom = 1;
}

function resizeCanvas() {
    if (!canvas || !canvas.parentElement) return;
    canvas.width = canvas.parentElement.clientWidth;
    canvas.height = canvas.parentElement.clientHeight - 80;
}

// ==========================================
// 5. INSPECTOR DRAWER & OSI PROTOCOL STEPPER
// ==========================================

function selectNode(node) {
    selectedNode = node;
    showDrawerNode(node);
}

function showDrawerNode(node) {
    if (!node || !drawerContent) return;
    if (drawerPlaceholder) drawerPlaceholder.style.display = 'none';
    drawerContent.style.display = 'block';

    if (inspectorDomainBadge) {
        inspectorDomainBadge.innerText = node.domain || node.label || 'Unknown';
    }

    const diag = node.diag || {};
    const pass = diag.is_ipv6_ready ?? false;
    const overall = diag.overall_status ?? 'UNKNOWN';

    // 4-Stage Breakdown & Baseline
    const stages = diag.stages || {};
    const notReachedTag = '<span class="stage-tag" style="background-color:var(--bg-muted); color:var(--text-muted); border-color:var(--border-default);">Not reached</span>';

    // Stage 1: DNS
    const dns = stages.dns;
    let dnsTagHtml = '';
    let dnsDetailsHtml = '';
    if (!dns) {
        dnsTagHtml = notReachedTag;
        dnsDetailsHtml = 'Stage not reached.';
    } else if (dns.has_aaaa) {
        const firstAaaa = dns.aaaa_records?.[0] || 'Present';
        dnsTagHtml = '<span class="stage-tag tag-pass">PASS</span>';
        dnsDetailsHtml = `IPv6: <span style="color:var(--text-primary);">${escapeHtml(firstAaaa)}</span> | Status: ${escapeHtml(dns.status || 'AAAA_EXISTS')}`;
    } else {
        dnsTagHtml = '<span class="stage-tag tag-fail">FAIL</span>';
        dnsDetailsHtml = `Status: ${escapeHtml(dns.error_detail || dns.status || 'Missing AAAA record in DNS zone.')}`;
    }

    // Stage 2: TCP
    const tcp = stages.tcp;
    let tcpTagHtml = '';
    let tcpDetailsHtml = '';
    if (!tcp) {
        tcpTagHtml = notReachedTag;
        tcpDetailsHtml = 'Stage not reached due to prior failure.';
    } else if (tcp.status === 'TCP_SUCCESS') {
        const rtt = tcp.rtt_ms ?? 0;
        tcpTagHtml = `<span class="stage-tag tag-pass">${rtt}ms</span>`;
        tcpDetailsHtml = `3-Way Handshake established on port ${diag.port || 443}. RTT: <span style="color:var(--text-primary);">${rtt}ms</span>`;
    } else {
        tcpTagHtml = `<span class="stage-tag tag-fail">${escapeHtml(tcp.error_code || 'FAIL')}</span>`;
        const codePrefix = tcp.error_code ? `[${escapeHtml(tcp.error_code)}] ` : '';
        tcpDetailsHtml = `Socket connect failed: ${codePrefix}${escapeHtml(tcp.error_detail || 'Connection failed')}`;
    }

    // Stage 3: TLS
    const tls = stages.tls;
    let tlsTagHtml = '';
    let tlsDetailsHtml = '';
    if (!tls) {
        tlsTagHtml = notReachedTag;
        tlsDetailsHtml = 'Stage not reached due to prior failure.';
    } else if (tls.status === 'TLS_SUCCESS') {
        tlsTagHtml = `<span class="stage-tag tag-pass">${escapeHtml(tls.tls_version || 'PASS')}</span>`;
        tlsDetailsHtml = `Protocol: ${escapeHtml(tls.tls_version || '--')} | Cipher: ${escapeHtml(tls.cipher || '--')}`;
    } else {
        tlsTagHtml = '<span class="stage-tag tag-fail">FAIL</span>';
        tlsDetailsHtml = `TLS handshake failed: ${escapeHtml(tls.error_detail || 'Handshake failed')}`;
    }

    // Stage 4: HTTP
    const http = stages.http;
    let httpTagHtml = '';
    let httpDetailsHtml = '';
    if (!http) {
        httpTagHtml = notReachedTag;
        httpDetailsHtml = 'Stage not reached due to prior failure.';
    } else if (http.status === 'HTTP_SUCCESS' || http.status === 'HTTP_4XX_CLIENT_ERROR') {
        const statusTag = http.http_status_code ? `HTTP ${http.http_status_code}` : 'PASS';
        httpTagHtml = `<span class="stage-tag tag-pass">${escapeHtml(statusTag)}</span>`;
        httpDetailsHtml = `${escapeHtml(http.status_line || `HTTP ${http.http_status_code || 200}`)} | TTFB: <span style="color:var(--text-primary);">${http.ttfb_ms ?? 0}ms</span>`;
    } else {
        const statusTag = http.http_status_code ? `HTTP ${http.http_status_code}` : 'FAIL';
        httpTagHtml = `<span class="stage-tag tag-fail">${escapeHtml(statusTag)}</span>`;
        const linePrefix = http.status_line ? `${escapeHtml(http.status_line)} - ` : '';
        httpDetailsHtml = `${linePrefix}${escapeHtml(http.error_detail || 'Server error or unroutable resource.')}`;
    }

    // Latency Box
    const v4Baseline = diag.ipv4_baseline;
    const hasV6Ttfb = http && http.ttfb_ms !== undefined && http.ttfb_ms !== null;
    const v6Ttfb = hasV6Ttfb ? http.ttfb_ms : null;
    const hasV4Tcp = v4Baseline && v4Baseline.tcp_success !== undefined && v4Baseline.tcp_success !== null;
    const v4TcpSuccess = hasV4Tcp ? v4Baseline.tcp_success : null;
    const showLatencyBox = hasV6Ttfb || hasV4Tcp;

    // Nameserver Audit (RFC 3901)
    const nsAudit = diag.ns_audit || (node.is_root ? currentAuditData?.metrics?.ns_audit : null);
    let nsCardHtml = '';
    if (nsAudit && nsAudit.total_nameservers > 0) {
        const nsPass = nsAudit.rfc3901_compliant;
        const nsTag = `<span class="stage-tag ${nsPass ? 'tag-pass' : (nsAudit.ipv6_nameservers_count > 0 ? 'tag-warn' : 'tag-fail')}">${nsAudit.ipv6_nameservers_count}/${nsAudit.total_nameservers} AAAA</span>`;
        const nsDesc = nsPass
            ? `Zone [${escapeHtml(nsAudit.apex_domain)}] has ≥2 IPv6-reachable nameservers (RFC 3901 compliant).`
            : (nsAudit.ipv6_nameservers_count > 0
                ? `Only ${nsAudit.ipv6_nameservers_count} of ${nsAudit.total_nameservers} authoritative nameservers have AAAA records. High risk of resolution failure for pure IPv6 recursive resolvers.`
                : `No authoritative nameserver has an AAAA record. Pure IPv6 recursive resolvers cannot resolve this zone.`);
        nsCardHtml = `
        <div class="stage-card" style="margin-top:8px; border-color:${nsPass ? 'var(--color-green-border)' : (nsAudit.ipv6_nameservers_count > 0 ? 'var(--color-amber-border)' : 'var(--color-red-border)')};">
            <div class="stage-top">
                <span class="stage-title">Authoritative NS (RFC 3901) <a href="https://datatracker.ietf.org/doc/html/rfc3901" target="_blank" rel="noopener noreferrer" class="rfc-pill" title="RFC 3901: DNS IPv6 Transport Operational Guidelines">RFC 3901</a></span>
                ${nsTag}
            </div>
            <div class="stage-details">${nsDesc}</div>
        </div>`;
    }

    // Hardcoded IPv4 Literal Alert (RFC 6052)
    const isIpv4Lit = Boolean(node.is_ipv4_literal || (/^(\d{1,3}\.){3}\d{1,3}$/.test(node.domain || '')));
    let ipv4LitCardHtml = '';
    if (isIpv4Lit) {
        ipv4LitCardHtml = `
        <div class="stage-card" style="margin-top:8px; border-color:var(--color-red-border); background-color:var(--color-red-bg);">
            <div class="stage-top">
                <span class="stage-title" style="color:var(--color-red);">Hardcoded IPv4 Literal <a href="https://datatracker.ietf.org/doc/html/rfc6052" target="_blank" rel="noopener noreferrer" class="rfc-pill" title="RFC 6052: IPv4-Embedded IPv6 Address Format">RFC 6052</a></span>
                <span class="stage-tag tag-fail">BYPASSES DNS</span>
            </div>
            <div class="stage-details" style="color:#ff7b72;">
                This dependency references a raw IPv4 literal address (${escapeHtml(node.domain)}). It completely bypasses DNS and fails immediately on pure IPv6 networks without NAT64 translation.
            </div>
        </div>`;
    }

    // Actionable CLI Probe Command
    const host = node.domain || 'target.domain';
    const firstAaaa = dns?.aaaa_records?.[0] || '';
    const connectHost = firstAaaa ? `[${firstAaaa}]` : host;

    let cliLabel = '';
    let cliCmd = '';
    if (!dns || !dns.has_aaaa) {
        cliLabel = 'DNS AAAA & DNSSEC Audit';
        cliCmd = `dig AAAA ${host} +dnssec +trace`;
    } else if (!tcp || tcp.status !== 'TCP_SUCCESS') {
        cliLabel = 'Raw IPv6 TCP Socket Handshake';
        cliCmd = `curl -6 --connect-timeout 4 -I -v https://${host}`;
    } else if (!tls || tls.status !== 'TLS_SUCCESS') {
        cliLabel = 'IPv6 TLS Certificate & SNI Handshake';
        cliCmd = `openssl s_client -6 -connect ${connectHost}:443 -servername ${host}`;
    } else {
        cliLabel = 'Strict IPv6 HTTP TTFB Latency Benchmark';
        cliCmd = `curl -6 -s -o /dev/null -w "HTTP: %{http_code} | TTFB: %{time_starttransfer}s | Total: %{time_total}s\\n" https://${host}`;
    }

    drawerContent.innerHTML = `
        <!-- Host Overview -->
        <div style="margin-bottom:14px;">
            <div style="font-size:0.95rem; font-weight:600; color:var(--text-primary); word-break:break-all;">${escapeHtml(node.domain)}</div>
            <div style="display:flex; gap:6px; margin-top:6px; flex-wrap:wrap;">
                <span class="badge ${pass ? 'badge-ready' : 'badge-v4only'}">${escapeHtml(overall)}</span>
                <span class="badge" style="background-color:var(--bg-muted); color:var(--text-secondary);">${node.isFirstParty ? '1st Party' : '3rd Party'}</span>
                ${node.is_root ? '<span class="badge badge-ready">Root Target</span>' : ''}
            </div>
        </div>

        <!-- 4-Stage OSI Protocol Pipeline -->
        <div style="font-size:0.72rem; font-weight:600; text-transform:uppercase; letter-spacing:0.4px; color:var(--text-muted); margin-bottom:8px;">
            OSI Protocol Stage Isolation
        </div>

        <!-- Stage 1: DNS -->
        <div class="stage-card">
            <div class="stage-top">
                <span class="stage-title">1. DNS Resolution (AAAA) <a href="https://datatracker.ietf.org/doc/html/rfc3596" target="_blank" rel="noopener noreferrer" class="rfc-pill" title="RFC 3596: DNS Extensions to Support IPv6">RFC 3596</a></span>
                ${dnsTagHtml}
            </div>
            <div class="stage-details">
                ${dnsDetailsHtml}
            </div>
        </div>

        <!-- Stage 2: TCP -->
        <div class="stage-card">
            <div class="stage-top">
                <span class="stage-title">2. Raw TCP SYN (AF_INET6) <a href="https://datatracker.ietf.org/doc/html/rfc8305" target="_blank" rel="noopener noreferrer" class="rfc-pill" title="RFC 8305: Happy Eyeballs Version 2">RFC 8305</a></span>
                ${tcpTagHtml}
            </div>
            <div class="stage-details">
                ${tcpDetailsHtml}
            </div>
        </div>

        <!-- Stage 3: TLS -->
        <div class="stage-card">
            <div class="stage-top">
                <span class="stage-title">3. TLS Handshake & SNI <a href="https://datatracker.ietf.org/doc/html/rfc8446" target="_blank" rel="noopener noreferrer" class="rfc-pill" title="RFC 8446: TLS 1.3">RFC 8446</a></span>
                ${tlsTagHtml}
            </div>
            <div class="stage-details">
                ${tlsDetailsHtml}
            </div>
        </div>

        <!-- Stage 4: HTTP -->
        <div class="stage-card">
            <div class="stage-top">
                <span class="stage-title">4. Strict HTTP/1.1 or H2 GET <a href="https://datatracker.ietf.org/doc/html/rfc9113" target="_blank" rel="noopener noreferrer" class="rfc-pill" title="RFC 9113: HTTP/2 Specification">RFC 9113</a></span>
                ${httpTagHtml}
            </div>
            <div class="stage-details">
                ${httpDetailsHtml}
            </div>
        </div>

        ${nsCardHtml}
        ${ipv4LitCardHtml}

        <!-- Dual-Path TTFB Comparison -->
        ${showLatencyBox ? `
        <div class="ttfb-box">
            <div style="font-size:0.72rem; font-weight:600; color:var(--color-blue); margin-bottom:6px;">Dual-Path Latency Benchmark</div>
            ${hasV4Tcp ? `
            <div style="font-size:0.72rem; color:var(--text-secondary); display:flex; justify-content:space-between; margin-bottom:2px;">
                <span>IPv4 TCP reachable:</span>
                <span class="font-mono ${v4TcpSuccess ? 'text-green' : 'text-red'}">${v4TcpSuccess ? 'yes' : 'no'}</span>
            </div>` : ''}
            ${hasV6Ttfb ? `
            <div style="font-size:0.72rem; color:var(--text-secondary); display:flex; justify-content:space-between;">
                <span>Pure IPv6 TTFB:</span>
                <span class="font-mono text-green">${v6Ttfb}ms</span>
            </div>` : `
            <div style="font-size:0.72rem; color:var(--text-secondary); display:flex; justify-content:space-between;">
                <span>Pure IPv6 TTFB:</span>
                <span class="font-mono text-red">Unreachable</span>
            </div>`}
        </div>` : ''}

        <!-- Actionable CLI Verification Console -->
        <div class="cli-console-box">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                <span style="font-size:0.70rem; font-weight:600; text-transform:uppercase; letter-spacing:0.3px; color:var(--color-blue);">
                    CLI Verification: ${escapeHtml(cliLabel)}
                </span>
                <button type="button" class="btn-copy-cli" id="btnCopyCliCmd" data-cmd="${escapeHtml(cliCmd)}">
                    Copy Command
                </button>
            </div>
            <pre class="cli-code-block font-mono"><code>${escapeHtml(cliCmd)}</code></pre>
            <div style="font-size:0.67rem; color:var(--text-muted); margin-top:4px;">
                Run directly in terminal to isolate transport layer and bypass browser Happy Eyeballs fallback.
            </div>
        </div>
    `;

    const copyBtn = drawerContent.querySelector('#btnCopyCliCmd');
    if (copyBtn) {
        copyBtn.addEventListener('click', () => {
            const cmd = copyBtn.dataset.cmd;
            if (cmd) {
                navigator.clipboard.writeText(cmd);
                const originalText = copyBtn.innerText;
                copyBtn.innerText = 'Copied!';
                copyBtn.style.color = '#3fb950';
                setTimeout(() => {
                    copyBtn.innerText = originalText;
                    copyBtn.style.color = '';
                }, 2000);
            }
        });
    }
}

// ==========================================
// 6. LIVE WIRE-LEVEL TERMINAL STREAM
// ==========================================

function initTerminalActions() {
    // Stage Tabs
    document.querySelectorAll('.stage-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.stage-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            activeTerminalStage = tab.dataset.stage;
            filterTerminalLines();
        });
    });

    // Clear Button
    document.getElementById('btnClearTerminal')?.addEventListener('click', () => {
        terminalLogs = [];
        if (terminalStream) terminalStream.innerHTML = '';
        logToTerminal('SYSTEM', 'Terminal stream cleared.');
    });

    // Copy Button
    document.getElementById('btnCopyTerminal')?.addEventListener('click', () => {
        const text = terminalLogs.map(l => `${l.time} [${l.stage}] ${l.msg}`).join('\n');
        navigator.clipboard.writeText(text).then(() => {
            const btn = document.getElementById('btnCopyTerminal');
            if (btn) {
                btn.innerText = 'Copied!';
                setTimeout(() => { btn.innerText = 'Copy Logs'; }, 1800);
            }
        });
    });
}

function logToTerminal(stage, msg, isPass = true) {
    if (!terminalStream) return;
    const now = new Date();
    const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}.${String(now.getMilliseconds()).padStart(3, '0')}`;

    terminalLogs.push({ time: timeStr, stage: stage, msg: msg, isPass: isPass });

    const line = document.createElement('div');
    line.className = 'terminal-row';
    line.dataset.stage = stage;

    let stageClass = 't-stage';
    let statusClass = isPass ? 't-pass' : 't-fail';

    line.innerHTML = `
        <span class="t-dim">${timeStr}</span>
        <span class="${stageClass}">[${stage}]</span>
        <span class="${statusClass}">${escapeHtml(msg)}</span>
    `;

    if (activeTerminalStage === 'ALL' || activeTerminalStage === stage) {
        line.style.display = 'block';
    } else {
        line.style.display = 'none';
    }

    terminalStream.appendChild(line);
    terminalStream.scrollTop = terminalStream.scrollHeight;
}

function filterTerminalLines() {
    if (!terminalStream) return;
    const lines = terminalStream.querySelectorAll('.terminal-row');
    lines.forEach(l => {
        const stage = l.dataset.stage;
        if (activeTerminalStage === 'ALL' || activeTerminalStage === stage) {
            l.style.display = 'block';
        } else {
            l.style.display = 'none';
        }
    });
    terminalStream.scrollTop = terminalStream.scrollHeight;
}

// ==========================================
// 7. 30-SITE NATIONAL BENCHMARK
// ==========================================

async function loadBenchmarkData() {
    try {
        const resp = await fetch('/api/benchmark');
        if (!resp.ok) throw new Error('Failed to fetch benchmark');
        const data = await resp.json();
        renderBenchmarkTab(data);
    } catch (err) {
        console.error('Error loading benchmark:', err);
    }
}

function renderBenchmarkTab(payload) {
    const sites = Array.isArray(payload.sites) ? payload.sites : [];
    const metadata = payload.metadata || {};
    const completedSites = sites.filter(s => s && s.metrics && !s.error);

    // 1. Average Readiness Score
    const avgScore = metadata.average_readiness_score_percent !== undefined
        ? `${metadata.average_readiness_score_percent}%`
        : (completedSites.length > 0
            ? `${Math.round(completedSites.reduce((acc, s) => acc + (s.metrics.readiness_score_percent || 0), 0) / completedSites.length)}%`
            : '--%');
    const avgEl = document.getElementById('benchAvgScore');
    if (avgEl) avgEl.innerText = avgScore;

    // 2. Sites Evaluated Count (Real completed count, no default to 30)
    const totalCount = metadata.total_targets_evaluated !== undefined
        ? metadata.total_targets_evaluated
        : completedSites.length;
    const totalEl = document.getElementById('benchTotalSites');
    if (totalEl) totalEl.innerText = totalCount;

    // 3. Leading Sector (from metadata.sector_averages or completed sites)
    let leadingSector = '--';
    const sectorAvgs = metadata.sector_averages;
    if (sectorAvgs && Object.keys(sectorAvgs).length > 0) {
        let maxAvg = -1;
        for (const [sec, avg] of Object.entries(sectorAvgs)) {
            if (avg > maxAvg) {
                maxAvg = avg;
                leadingSector = sec;
            }
        }
    } else if (completedSites.length > 0) {
        const sSums = {};
        completedSites.forEach(s => {
            const sec = s.sector || 'General';
            if (!sSums[sec]) sSums[sec] = { total: 0, count: 0 };
            sSums[sec].total += (s.metrics.readiness_score_percent || 0);
            sSums[sec].count += 1;
        });
        let maxAvg = -1;
        for (const [sec, obj] of Object.entries(sSums)) {
            const avg = obj.total / obj.count;
            if (avg > maxAvg) {
                maxAvg = avg;
                leadingSector = sec;
            }
        }
    }
    const leadingEl = document.getElementById('benchLeadingSector');
    if (leadingEl) leadingEl.innerText = leadingSector;

    // 4. Primary Bottleneck (highest sum across DNS, TCP, TLS, HTTP)
    const stageSums = { DNS: 0, TCP: 0, TLS: 0, HTTP: 0 };
    completedSites.forEach(s => {
        const sf = s.metrics?.stage_failures || {};
        for (const stage of ['DNS', 'TCP', 'TLS', 'HTTP']) {
            stageSums[stage] += (sf[stage] || 0);
        }
    });
    let maxFail = -1;
    let topStage = 'None';
    for (const stage of ['DNS', 'TCP', 'TLS', 'HTTP']) {
        if (stageSums[stage] > maxFail) {
            maxFail = stageSums[stage];
            topStage = stage;
        }
    }
    const stageLabels = {
        DNS: 'DNS Resolution',
        TCP: 'TCP Transport',
        TLS: 'TLS Handshake',
        HTTP: 'HTTP Retrieval',
        None: 'None'
    };
    const bottleneckEl = document.getElementById('benchPrimaryBottleneck');
    if (bottleneckEl) {
        bottleneckEl.innerText = maxFail > 0 ? (stageLabels[topStage] || topStage) : 'None';
    }

    // 5. Dynamic Sector Filter Pills
    renderSectorFilterPills(sites);

    // 6. Sector Bar Chart
    renderSectorBarChart(sites);

    // 7. Protocol Failure Taxonomy
    renderTaxonomyChart(sites);

    // 8. Benchmark Table
    renderBenchmarkTable(sites);
}

function renderSectorFilterPills(sites) {
    const container = document.getElementById('sectorFilterPills');
    if (!container) return;

    const distinctSectors = Array.from(
        new Set((sites || []).map(s => s.sector).filter(Boolean))
    ).sort();

    let html = `<button class="filter-pill active" data-sector="ALL">All Sectors</button>`;
    distinctSectors.forEach(sec => {
        html += `<button class="filter-pill" data-sector="${escapeHtml(sec)}">${escapeHtml(sec)}</button>`;
    });
    container.innerHTML = html;

    // Attach click listener once via delegation on container
    if (!container.dataset.bound) {
        container.dataset.bound = 'true';
        container.addEventListener('click', (e) => {
            const btn = e.target.closest('.filter-pill');
            if (!btn) return;
            container.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const sector = btn.dataset.sector;
            filterBenchmarkTable(sector);
        });
    }
}

function renderSectorBarChart(sites) {
    const container = document.getElementById('sectorBarChart');
    if (!container) return;
    container.innerHTML = '';

    const completed = (sites || []).filter(s => s && s.metrics && !s.error);
    if (completed.length === 0) {
        container.innerHTML = '<div class="font-mono text-muted" style="padding:16px; text-align:center;">No sector evaluation data available.</div>';
        return;
    }

    // Group scores by sector
    const sectors = {};
    completed.forEach(r => {
        const sec = r.sector || 'General';
        if (!sectors[sec]) sectors[sec] = { totalScore: 0, count: 0 };
        sectors[sec].totalScore += (r.metrics.readiness_score_percent || 0);
        sectors[sec].count += 1;
    });

    const sectorList = Object.entries(sectors).map(([sec, val]) => {
        const avg = Math.round(val.totalScore / Math.max(val.count, 1));
        return { sector: sec, avg: avg };
    });

    // Sort descending by average
    sectorList.sort((a, b) => b.avg - a.avg);

    sectorList.forEach(({ sector, avg }) => {
        const color = avg >= 70 ? 'var(--color-green)' : (avg >= 40 ? 'var(--color-amber)' : 'var(--color-red)');
        const row = document.createElement('div');
        row.className = 'sector-row';
        row.innerHTML = `
            <span class="sector-label" title="${escapeHtml(sector)}">${escapeHtml(sector)}</span>
            <div class="sector-track">
                <div class="sector-fill" style="width:${avg}%; background-color:${color};"></div>
            </div>
            <span class="sector-percent">${avg}%</span>
        `;
        container.appendChild(row);
    });
}

function renderTaxonomyChart(sites) {
    const container = document.getElementById('failureTaxonomyChart');
    if (!container) return;

    const completed = (sites || []).filter(s => s && s.metrics && !s.error);
    if (completed.length === 0) {
        container.innerHTML = '<div class="font-mono text-muted" style="padding:16px; text-align:center;">No protocol failure data available.</div>';
        return;
    }

    let dnsFailures = 0;
    let tcpFailures = 0;
    let tlsFailures = 0;
    let httpFailures = 0;

    completed.forEach(r => {
        const sf = r.metrics?.stage_failures || {};
        dnsFailures += (sf.DNS || 0);
        tcpFailures += (sf.TCP || 0);
        tlsFailures += (sf.TLS || 0);
        httpFailures += (sf.HTTP || 0);
    });

    container.innerHTML = `
        <div class="taxonomy-blocks">
            <div class="taxonomy-card">
                <div class="tax-title">DNS Stage Failures</div>
                <div class="tax-val text-red">${dnsFailures}</div>
                <div class="tax-note">Missing AAAA / NXDOMAIN / NODATA</div>
            </div>
            <div class="taxonomy-card">
                <div class="tax-title">TCP Stage Failures</div>
                <div class="tax-val text-amber">${tcpFailures}</div>
                <div class="tax-note">Handshake Timeout / Refused / No Route</div>
            </div>
            <div class="taxonomy-card">
                <div class="tax-title">TLS Stage Failures</div>
                <div class="tax-val text-amber">${tlsFailures}</div>
                <div class="tax-note">Certificate / SNI / Handshake Failures</div>
            </div>
            <div class="taxonomy-card">
                <div class="tax-title">HTTP Stage Failures</div>
                <div class="tax-val text-red">${httpFailures}</div>
                <div class="tax-note">HTTP 5xx Server Errors</div>
            </div>
        </div>
    `;
}

function renderBenchmarkTable(sites) {
    const tbody = document.getElementById('benchmarkTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';

    if (!sites || sites.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" class="table-empty font-mono">No benchmark evaluation results available.</td></tr>`;
        return;
    }

    sites.forEach(r => {
        const tr = document.createElement('tr');
        tr.dataset.sector = r.sector || 'General';

        if (r.error || !r.metrics) {
            tr.style.opacity = '0.65';
            tr.innerHTML = `
                <td>
                    <div style="font-weight:600; color:var(--text-secondary);">${escapeHtml(r.name || r.id || 'Unknown')}</div>
                    <div style="font-family:var(--font-mono); font-size:0.7rem; color:var(--text-muted);">${escapeHtml(r.url || '')}</div>
                </td>
                <td><span class="badge" style="background-color:var(--bg-muted); color:var(--text-secondary);">${escapeHtml(r.sector || '')}</span></td>
                <td colspan="5" class="font-mono text-red" style="font-size:0.75rem;">Audit Error: ${escapeHtml(r.error || 'Evaluation failed')}</td>
                <td>
                    <button class="btn btn-sm btn-secondary btn-benchmark-audit" data-url="${escapeHtml(r.url || '')}">Retry</button>
                </td>
            `;
        } else {
            const metrics = r.metrics || {};
            const score = metrics.readiness_score_percent ?? 0;
            const blast = metrics.blast_radius_percent ?? (100 - score);
            const apexAaaa = r.apex_audit?.has_aaaa ?? false;

            tr.innerHTML = `
                <td>
                    <div style="font-weight:600; color:var(--text-primary);">${escapeHtml(r.name || r.id)}</div>
                    <div style="font-family:var(--font-mono); font-size:0.7rem; color:var(--text-muted);">${escapeHtml(r.url || '')}</div>
                </td>
                <td><span class="badge" style="background-color:var(--bg-muted); color:var(--text-secondary);">${escapeHtml(r.sector || '')}</span></td>
                <td>${apexAaaa ? '<span class="text-green font-mono">Present</span>' : '<span class="text-red font-mono">Missing</span>'}</td>
                <td class="font-mono">${metrics.total_resources ?? '--'}</td>
                <td>
                    <span class="font-mono ${score >= 70 ? 'text-green' : (score >= 40 ? 'text-amber' : 'text-red')}" style="font-weight:600;">
                        ${score}%
                    </span>
                </td>
                <td class="font-mono text-amber">${blast}%</td>
                <td class="font-mono text-red">${metrics.ipv4_only_count ?? 0}</td>
                <td>
                    <button class="btn btn-sm btn-secondary btn-benchmark-audit" data-url="${escapeHtml(r.url || '')}">Audit</button>
                </td>
            `;
        }

        const auditBtn = tr.querySelector('.btn-benchmark-audit');
        if (auditBtn) {
            auditBtn.addEventListener('click', () => {
                const targetUrl = auditBtn.dataset.url;
                if (targetUrl) {
                    triggerBenchmarkAudit(targetUrl);
                }
            });
        }
        tbody.appendChild(tr);
    });
}

function filterBenchmarkTable(sector) {
    const rows = document.querySelectorAll('#benchmarkTableBody tr');
    rows.forEach(r => {
        if (sector === 'ALL' || r.dataset.sector === sector) {
            r.style.display = '';
        } else {
            r.style.display = 'none';
        }
    });
}

window.triggerBenchmarkAudit = function(url) {
    // Switch to Tab 1
    const liveTab = document.querySelector('.nav-tab[data-target="liveAuditPanel"]');
    if (liveTab) liveTab.click();
    if (urlInput) urlInput.value = url;
    runAudit(url);
};

// ==========================================
// 8. CONTROLLED TESTBED VERIFICATION
// ==========================================

async function loadTestbedVerification() {
    try {
        const resp = await fetch('/api/testbed');
        if (!resp.ok) throw new Error('Testbed fetch failed');
        const data = await resp.json();
        renderTestbedTab(data);
    } catch (err) {
        console.error('Testbed error:', err);
    }
}

function renderTestbedTab(data) {
    const metrics = data.metrics || {};
    const verified = metrics.detection_rate_verified === true;

    // Status Badge
    const badge = document.getElementById('testbedStatusBadge');
    if (badge) {
        badge.className = `status-pill ${verified ? 'status-ready' : 'status-error'}`;
        if (verified) {
            badge.innerText = `Verified Ground Truth (100% Precision & Recall)`;
        } else {
            badge.innerText = `Unverified: P=${metrics.precision_percent ?? 0}% R=${metrics.recall_percent ?? 0}%`;
        }
    }

    // Four Metric Cards
    const precEl = document.getElementById('testbedPrecision');
    if (precEl) precEl.innerText = metrics.precision_percent !== undefined ? `${metrics.precision_percent}%` : '--';

    const recallEl = document.getElementById('testbedRecall');
    if (recallEl) recallEl.innerText = metrics.recall_percent !== undefined ? `${metrics.recall_percent}%` : '--';

    const accEl = document.getElementById('testbedAccuracy');
    if (accEl) accEl.innerText = metrics.overall_accuracy_percent !== undefined ? `${metrics.overall_accuracy_percent}%` : '--';

    const portEl = document.getElementById('testbedPort');
    if (portEl) portEl.innerText = ':8888';

    // Evaluations Table
    const tbody = document.getElementById('testbedTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';

    const evaluations = data.evaluations || [];
    if (evaluations.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="table-empty font-mono">No testbed evaluation records available.</td></tr>`;
        return;
    }

    evaluations.forEach(e => {
        const tr = document.createElement('tr');

        let resultBadge = '';
        if (e.evaluation_result === 'CORRECT_DETECTION' || e.evaluation_result === 'CORRECT_COMPLIANT') {
            resultBadge = `<span class="badge badge-ready font-mono">${escapeHtml(e.evaluation_result)}</span>`;
        } else if (e.evaluation_result === 'MISSED_DETECTION') {
            resultBadge = `<span class="badge badge-v4only font-mono">${escapeHtml(e.evaluation_result)}</span>`;
        } else if (e.evaluation_result === 'FALSE_ALARM') {
            resultBadge = `<span class="badge badge-broken font-mono">${escapeHtml(e.evaluation_result)}</span>`;
        } else {
            resultBadge = `<span class="badge font-mono" style="background-color:var(--bg-muted); color:var(--text-secondary);">${escapeHtml(e.evaluation_result || '--')}</span>`;
        }

        tr.innerHTML = `
            <td><code class="font-mono text-blue">${escapeHtml(e.url_path)}</code></td>
            <td style="color:var(--text-secondary);">${escapeHtml(e.description)}</td>
            <td><span class="badge" style="background-color:var(--bg-muted); color:var(--text-muted);">${escapeHtml(e.expected_status)}</span></td>
            <td><span class="badge ${e.status_match ? 'badge-ready' : 'badge-v4only'}">${escapeHtml(e.detected_status)}</span></td>
            <td><code class="font-mono ${e.stage_match ? 'text-green' : 'text-amber'}">${escapeHtml(e.detected_stage || '--')}</code></td>
            <td>${resultBadge}</td>
        `;
        tbody.appendChild(tr);
    });
}

function initTestbedActions() {
    const btn = document.getElementById('btnReverifyTestbed');
    if (btn && !btn.dataset.bound) {
        btn.dataset.bound = 'true';
        btn.addEventListener('click', async () => {
            btn.disabled = true;
            const badge = document.getElementById('testbedStatusBadge');
            if (badge) badge.innerText = 'Re-verifying testbed...';
            try {
                await loadTestbedVerification();
            } finally {
                btn.disabled = false;
            }
        });
    }
}

// ==========================================
// 9. CLIENT TELEMETRY CONTEXT
// ==========================================

async function loadTelemetryContext() {
    try {
        const resp = await fetch('/api/telemetry');
        if (!resp.ok) return;
        const data = await resp.json();

        const pub = data.public_telemetry || {};
        const local = data.local_interfaces || {};
        const dns = data.dns_telemetry || {};

        // Update nav snippet
        const snippet = document.getElementById('navTelemetrySnippet');
        if (snippet) {
            const v6Status = data.has_native_ipv6 ? 'Native IPv6' : 'IPv4 only';
            const asnPart = pub.asn ? `${pub.asn} / ${v6Status}` : v6Status;
            snippet.innerText = `Telemetry: ${asnPart}`;
        }

        // Populate Telemetry Box
        const box = document.getElementById('telemetryBox');
        if (box) {
            // ASN and organization
            let asnDisplay = 'Unavailable';
            if (pub.asn && pub.as_org) {
                asnDisplay = `${pub.asn} (${pub.as_org})`;
            } else if (pub.asn) {
                asnDisplay = pub.asn;
            } else if (pub.as_org) {
                asnDisplay = pub.as_org;
            }

            // Location
            let locDisplay = 'Unavailable';
            if (pub.city && pub.country) {
                locDisplay = `${pub.city}, ${pub.country}`;
            } else if (pub.country) {
                locDisplay = pub.country;
            } else if (pub.city) {
                locDisplay = pub.city;
            }

            // Local IPv4
            const v4Display = local.ipv4 || 'Unavailable';

            // Local IPv6
            const v6Display = local.ipv6 || 'Unavailable';

            // DNS Resolver & latency
            let dnsDisplay = 'Unavailable';
            if (dns.primary_resolver) {
                if (dns.resolver_latency_ms !== null && dns.resolver_latency_ms !== undefined) {
                    dnsDisplay = `${dns.primary_resolver} (RTT: ${dns.resolver_latency_ms}ms)`;
                } else {
                    dnsDisplay = dns.primary_resolver;
                }
            }

            // Native IPv6 status
            const nativeV6Display = data.has_native_ipv6 ? 'Active (Native IPv6)' : 'Inactive (IPv4 Only)';

            box.innerHTML = `
                <div class="telemetry-card font-mono">
                    <span class="t-label">Autonomous System (ASN)</span>
                    <span class="t-value">${escapeHtml(asnDisplay)}</span>
                </div>
                <div class="telemetry-card font-mono">
                    <span class="t-label">Public Geolocation</span>
                    <span class="t-value">${escapeHtml(locDisplay)}</span>
                </div>
                <div class="telemetry-card font-mono">
                    <span class="t-label">Local IPv4 Gateway</span>
                    <span class="t-value">${escapeHtml(v4Display)}</span>
                </div>
                <div class="telemetry-card font-mono">
                    <span class="t-label">Local IPv6 Address</span>
                    <span class="t-value ${local.ipv6 ? 'text-green' : ''}">${escapeHtml(v6Display)}</span>
                </div>
                <div class="telemetry-card font-mono">
                    <span class="t-label">DNS Resolver</span>
                    <span class="t-value">${escapeHtml(dnsDisplay)}</span>
                </div>
                <div class="telemetry-card font-mono">
                    <span class="t-label">Native IPv6 Stack</span>
                    <span class="t-value ${data.has_native_ipv6 ? 'text-green' : 'text-amber'}">${escapeHtml(nativeV6Display)}</span>
                </div>
                <div class="telemetry-card font-mono">
                    <span class="t-label">Measurement Engine</span>
                    <span class="t-value">Playwright Chromium Headless + dnspython Wire Probes</span>
                </div>
                <div class="telemetry-card font-mono">
                    <span class="t-label">Decoupled Dual-Stack</span>
                    <span class="t-value text-blue">Happy-Eyeballs Decoupled AF_INET6 Socket Binding</span>
                </div>
            `;
        }
    } catch (err) {
        console.error('Telemetry error:', err);
    }
}

// Utilities
function truncate(str, max) {
    if (!str) return '';
    return str.length > max ? str.slice(0, max - 1) + '...' : str;
}

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
