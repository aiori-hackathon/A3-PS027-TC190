/**
 * IPv6 Readiness Inspector - Popup Script
 * Interacts with background service worker to display live tab network data,
 * remote IP addresses, and allows 1-click deep multi-stage OSI auditing.
 */

const LOCAL_AUDITOR_URL = 'http://localhost:8000';

let currentData = null;
let activeFilter = 'all';

document.addEventListener('DOMContentLoaded', async () => {
    // 1. Get current active tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) return;

    const domainEl = document.getElementById('currentDomain');
    try {
        const u = new URL(tab.url || '');
        domainEl.innerText = u.hostname || tab.title || 'Blank Tab';
    } catch {
        domainEl.innerText = tab.title || 'Chrome Page';
    }

    // 2. Request data from service worker
    chrome.runtime.sendMessage({ action: 'getTabData', tabId: tab.id }, (response) => {
        if (response && response.data) {
            currentData = response.data;
            renderData(response.data);
        } else {
            renderEmpty();
        }
    });

    // 3. Setup event listeners
    setupEvents(tab);
});

function setupEvents(tab) {
    // Deep Audit Button
    document.getElementById('btnDeepAudit')?.addEventListener('click', async () => {
        const targetUrl = tab.url;
        // Open web dashboard with target pre-filled
        const auditorPage = `${LOCAL_AUDITOR_URL}/`;
        await chrome.tabs.create({ url: auditorPage });
    });

    // Dashboard link
    document.getElementById('btnOpenDashboard')?.addEventListener('click', async (e) => {
        e.preventDefault();
        await chrome.tabs.create({ url: LOCAL_AUDITOR_URL });
    });

    // Reload Tab button
    document.getElementById('btnReloadTab')?.addEventListener('click', async () => {
        if (tab.id) {
            await chrome.tabs.reload(tab.id);
            window.close();
        }
    });

    // Filter pills
    document.querySelectorAll('.pill[data-filter]').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.pill[data-filter]').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            activeFilter = btn.dataset.filter;
            filterDomainList();
        });
    });

    // Search box
    document.getElementById('domainSearch')?.addEventListener('input', () => {
        filterDomainList();
    });
}

function renderData(data) {
    const scoreVal = document.getElementById('scoreValue');
    const scoreSub = document.getElementById('scoreSub');
    const apexBadge = document.getElementById('apexIpBadge');
    const countV6 = document.getElementById('countV6');
    const countV4 = document.getElementById('countV4');
    const countTotal = document.getElementById('countTotal');

    const score = data.score ?? 0;
    scoreVal.innerText = `${score}%`;
    scoreVal.className = `score-number font-mono ${score >= 75 ? 'text-green' : (score > 0 ? 'text-amber' : 'text-red')}`;

    if (!data.isApexV6 && data.apexIp) {
        scoreSub.innerText = 'Apex host lacks IPv6 reachability';
    } else if (score === 100) {
        scoreSub.innerText = '100% Pure IPv6 compliance';
    } else {
        scoreSub.innerText = `${data.v4Count} IPv4 dependencies detected`;
    }

    if (data.apexIp) {
        apexBadge.innerText = data.apexIp;
        apexBadge.className = `badge-tag font-mono ${data.isApexV6 ? 'badge-v6' : 'badge-v4'}`;
        apexBadge.title = `${data.apexIp} (${data.isApexV6 ? 'IPv6' : 'IPv4'})`;
    } else {
        apexBadge.innerText = 'Cached / Local';
    }

    countV6.innerText = data.v6Count || 0;
    countV4.innerText = data.v4Count || 0;
    countTotal.innerText = data.totalCount || 0;

    renderDomainList(data.domains || {});
}

function renderEmpty() {
    const scoreVal = document.getElementById('scoreValue');
    scoreVal.innerText = '--%';
    scoreVal.className = 'score-number font-mono';
    document.getElementById('scoreSub').innerText = 'Reload tab to capture network trace';
}

function renderDomainList(domainsMap) {
    const container = document.getElementById('domainList');
    if (!container) return;
    container.innerHTML = '';

    const list = Object.values(domainsMap);
    if (list.length === 0) {
        container.innerHTML = '<div class="empty-state">No hosts recorded for this tab yet. Reload the page to inspect.</div>';
        return;
    }

    // Sort by count desc
    list.sort((a, b) => b.count - a.count);

    list.forEach(item => {
        const row = document.createElement('div');
        row.className = 'domain-row';
        row.dataset.domain = item.domain.toLowerCase();
        row.dataset.v6 = item.isV6 ? 'true' : 'false';

        row.innerHTML = `
            <div class="domain-left">
                <span class="domain-name font-mono" title="${escapeHtml(item.domain)}">${escapeHtml(item.domain)}</span>
                <span class="domain-ip font-mono">${escapeHtml(item.ip || 'Cached')}</span>
            </div>
            <div class="domain-right">
                <span class="badge-tag font-mono ${item.isV6 ? 'badge-v6' : 'badge-v4'}">${item.isV6 ? 'IPv6' : 'IPv4'}</span>
                <span class="domain-count font-mono">${item.count}</span>
            </div>
        `;
        container.appendChild(row);
    });

    filterDomainList();
}

function filterDomainList() {
    const query = document.getElementById('domainSearch')?.value.toLowerCase().trim() || '';
    const rows = document.querySelectorAll('.domain-row');

    rows.forEach(r => {
        const domain = r.dataset.domain || '';
        const isV6 = r.dataset.v6 === 'true';

        let matchesFilter = true;
        if (activeFilter === 'v4' && isV6) matchesFilter = false;
        if (activeFilter === 'v6' && !isV6) matchesFilter = false;

        let matchesQuery = domain.includes(query);

        r.style.display = (matchesFilter && matchesQuery) ? 'flex' : 'none';
    });
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
