/**
 * IPv6 Readiness Inspector - Background Service Worker (Manifest V3)
 * Intercepts real-time browser network transactions via chrome.webRequest,
 * identifies IPv4 vs IPv6 remote addresses, and computes tab readiness scores.
 */

// Helper to determine if an IP address is IPv6
function isIPv6Address(ip) {
    if (!ip) return false;
    // IPv6 addresses contain colons (e.g. 2404:6800:4009:803::200e)
    return ip.includes(':');
}

// Extract hostname domain from URL
function getHostname(url) {
    try {
        const u = new URL(url);
        return u.hostname;
    } catch {
        return '';
    }
}

// Reset data for a given tab
async function resetTabData(tabId) {
    const key = `tab_${tabId}`;
    await chrome.storage.session.remove(key);
    try {
        await chrome.action.setBadgeText({ tabId, text: '' });
    } catch {}
}

// Handle tab navigation start
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo) => {
    if (changeInfo.status === 'loading') {
        await resetTabData(tabId);
    }
});

// Handle tab close
chrome.tabs.onRemoved.addListener(async (tabId) => {
    await resetTabData(tabId);
});

// Intercept HTTP/HTTPS responses to capture remote IP
chrome.webRequest.onResponseStarted.addListener(
    async (details) => {
        const tabId = details.tabId;
        if (tabId < 0) return; // Skip internal/background requests

        const url = details.url;
        if (url.startsWith('chrome-extension://') || url.startsWith('chrome://')) return;

        const remoteIp = details.ip || '';
        const isV6 = isIPv6Address(remoteIp);
        const domain = getHostname(url);
        const isMainFrame = details.type === 'main_frame';

        const storageKey = `tab_${tabId}`;
        const stored = await chrome.storage.session.get(storageKey);
        const tabData = stored[storageKey] || {
            tabId,
            mainUrl: '',
            apexDomain: '',
            apexIp: '',
            isApexV6: false,
            resources: [],
            domains: {},
            totalCount: 0,
            v6Count: 0,
            v4Count: 0
        };

        if (isMainFrame) {
            tabData.mainUrl = url;
            tabData.apexDomain = domain;
            tabData.apexIp = remoteIp;
            tabData.isApexV6 = isV6;
        }

        // Record resource
        tabData.resources.push({
            url,
            domain,
            ip: remoteIp,
            isV6,
            type: details.type,
            statusCode: details.statusCode,
            fromCache: details.fromCache ?? false
        });

        // Record domain aggregation
        if (domain) {
            if (!tabData.domains[domain]) {
                tabData.domains[domain] = {
                    domain,
                    ip: remoteIp,
                    isV6,
                    count: 0
                };
            }
            tabData.domains[domain].count += 1;
        }

        tabData.totalCount += 1;
        if (isV6) {
            tabData.v6Count += 1;
        } else if (remoteIp) {
            tabData.v4Count += 1;
        }

        // Calculate score
        const subresourceRate = tabData.totalCount > 0 ? Math.round((tabData.v6Count / tabData.totalCount) * 100) : 0;
        // SAP Webres6 principle: if apex is not v6, site cannot load in pure IPv6
        const overallScore = tabData.isApexV6 ? subresourceRate : 0;
        tabData.score = overallScore;
        tabData.subresourceRate = subresourceRate;

        // Persist to session storage
        await chrome.storage.session.set({ [storageKey]: tabData });

        // Update badge
        try {
            const badgeText = `${overallScore}%`;
            await chrome.action.setBadgeText({ tabId, text: badgeText });
            const badgeColor = overallScore >= 75 ? '#2ea043' : (overallScore > 0 ? '#d29922' : '#f85149');
            await chrome.action.setBadgeBackgroundColor({ tabId, color: badgeColor });
        } catch {}
    },
    { urls: ['<all_urls>'] }
);

// Listen for messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'getTabData') {
        (async () => {
            const tabId = message.tabId;
            const storageKey = `tab_${tabId}`;
            const stored = await chrome.storage.session.get(storageKey);
            sendResponse({ data: stored[storageKey] || null });
        })();
        return true; // Keep channel open for async response
    }
});
