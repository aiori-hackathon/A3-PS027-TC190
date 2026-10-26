# Privacy Policy for IPv6 Readiness Auditor

**Effective Date:** October 26, 2026  
**Last Updated:** October 26, 2026  

## 1. Overview
The **IPv6 Readiness Auditor** Chrome Extension (Manifest V3) is a developer and network analysis utility designed to measure the IPv6 reachability of websites and their sub-resource dependencies directly within the browser side panel.

We believe strongly in user privacy: **the extension does not collect, log, track, sell, or transmit any personal information or browsing history.**

---

## 2. Information We Handle and How It Is Used

### A. Network Request Inspection (`webRequest`)
- **What is accessed:** The extension passively monitors web requests made by the active browser tab to inspect the destination remote IP address (`details.ip`) and domain name.
- **Purpose:** To classify whether each loaded sub-resource (scripts, stylesheets, images, fonts, API endpoints) connects over IPv6 or IPv4.
- **Retention:** This diagnostic data is processed entirely in-memory and ephemerally cached in `chrome.storage.session` for the active tab. It is immediately discarded when the tab is closed or navigated.

### B. Active Tab Information (`tabs` and `activeTab`)
- **What is accessed:** The active tab's URL and title upon user interaction.
- **Purpose:** To trigger audits for the user's current webpage and dock the analysis in the Chrome Side Panel.
- **Retention:** Stored locally in session memory only during the user's active audit session.

### C. Local Preferences (`storage`)
- **What is stored:** Diagnostic caching and interface display preferences (e.g., active tab selection, filter states).
- **Location:** Stored strictly on the user's device using `chrome.storage.local` and `chrome.storage.session`. No data is synced to cloud servers or third parties.

---

## 3. Data Collection and Transmission
- **No Personal Identifiers:** We do not collect names, email addresses, cookies, authentication tokens, form inputs, or search queries.
- **No Third-Party Analytics:** We do not include third-party trackers, telemetry libraries (e.g., Google Analytics, Mixpanel), or advertising SDKs.
- **No External Data Transmission:** The extension never transmits inspected URLs, IP addresses, or browsing history to external servers. All diagnostics run locally in the browser or against the user's optional local testbed daemon (`http://localhost:8000`).

---

## 4. User Controls and Data Deletion
- Users can clear all cached diagnostics at any time by closing the side panel or navigating to a new page.
- Uninstalling the extension completely removes all associated storage and permissions from the user's device.

---

## 5. Contact Information
If you have any questions or feedback regarding this Privacy Policy or the security of the extension, please contact the maintainers:
- **Project Team:** Team A3-PS027-TC190
- **Repository:** https://github.com/
- **Issue Tracker:** https://github.com/issues
