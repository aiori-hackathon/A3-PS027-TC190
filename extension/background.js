/**
 * AIORI PS-027 IPv6 Website & Dependency Readiness Auditor
 * Background Service Worker (Manifest V3)
 *
 * Responsibilities:
 * 1. Enables 1-click Side Panel docking on action click via chrome.sidePanel API
 * 2. Passively inspects live tab network requests via chrome.webRequest to identify IPv4 vs IPv6 remote IPs
 * 3. Dynamically computes the SAP Webres6 readiness score and updates toolbar badges in real time
 * 4. Serves tab session data to the Side Panel application
 */

// Configure side panel to open on action click
if (chrome.sidePanel && chrome.sidePanel.setPanelBehavior) {
    chrome.sidePanel
        .setPanelBehavior({ openPanelOnActionClick: true })
        .catch((err) => console.warn('setPanelBehavior error:', err));
}

chrome.runtime.onInstalled.addListener(() => {
    if (chrome.sidePanel && chrome.sidePanel.setPanelBehavior) {
        chrome.sidePanel
            .setPanelBehavior({ openPanelOnActionClick: true })
            .catch((err) => console.warn('setPanelBehavior onInstalled error:', err));
    }
});

// Fallback if setPanelBehavior is not supported on older Chromium
if (chrome.action && chrome.action.onClicked) {
    chrome.action.onClicked.addListener(async (tab) => {
        if (chrome.sidePanel && chrome.sidePanel.open) {
            try {
                await chrome.sidePanel.open({ windowId: tab.windowId });
            } catch (err) {
                console.warn('sidePanel.open error:', err);
            }
        }
    });
}

// Helper to determine if an IP address is IPv6
function isIPv6Address(ip) {
    if (!ip) return false;
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
    try {
        await chrome.storage.session.remove(key);
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
        if (tabId < 0) return; // Skip background / extension requests

        const url = details.url;
        if (url.startsWith('chrome-extension://') || url.startsWith('chrome://')) return;

        const remoteIp = details.ip || '';
        const isV6 = isIPv6Address(remoteIp);
        const domain = getHostname(url);
        const isMainFrame = details.type === 'main_frame';

        const storageKey = `tab_${tabId}`;
        let tabData;
        try {
            const stored = await chrome.storage.session.get(storageKey);
            tabData = stored[storageKey] || {
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
        } catch {
            return;
        }

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

        // Calculate SAP Webres6 score
        const subresourceRate = tabData.totalCount > 0 ? Math.round((tabData.v6Count / tabData.totalCount) * 100) : 0;
        // Core SAP Webres6 rule: If apex lacks IPv6, site is unresolvable in IPv6-only networks
        const overallScore = tabData.isApexV6 ? subresourceRate : 0;
        tabData.score = overallScore;
        tabData.subresourceRate = subresourceRate;

        // Persist to session storage
        try {
            await chrome.storage.session.set({ [storageKey]: tabData });

            // Update badge
            const badgeText = `${overallScore}%`;
            await chrome.action.setBadgeText({ tabId, text: badgeText });
            const badgeColor = overallScore >= 75 ? '#2ea043' : (overallScore > 0 ? '#d29922' : '#f85149');
            await chrome.action.setBadgeBackgroundColor({ tabId, color: badgeColor });
        } catch {}
    },
    { urls: ['<all_urls>'] }
);

// Listen for messages from Side Panel and Popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'getTabData') {
        (async () => {
            try {
                const tabId = message.tabId;
                const storageKey = `tab_${tabId}`;
                const stored = await chrome.storage.session.get(storageKey);
                sendResponse({ data: stored[storageKey] || null });
            } catch (err) {
                sendResponse({ error: err.message, data: null });
            }
        })();
        return true; // Keep message channel open for async response
    }

    if (message.action === 'getActiveTab') {
        (async () => {
            try {
                const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
                sendResponse({ tab: tab || null });
            } catch (err) {
                sendResponse({ error: err.message, tab: null });
            }
        })();
        return true;
    }
});
