# Chrome Web Store Listing & Compliance

## Extension Metadata
- **Name**: IPv6 Readiness Inspector
- **Version**: 1.0.0
- **Category**: Developer Tools / Network & Performance
- **Short Description**: Inspects real-time IPv6 and IPv4 socket reachability of the active webpage and all sub-resource dependencies.
- **Detailed Description**:
  IPv6 Readiness Inspector analyzes the real-world IPv6 reachability of modern websites and web applications directly inside Google Chrome.

  Modern web applications rely on dozens of third-party dependencies, including content delivery networks (CDNs), stylesheets, fonts, and API endpoints. If any critical sub-resource remains IPv4-only, users on pure IPv6 networks face broken page layouts, hanging scripts, and degraded performance.

  Features:
  - Real-time network request socket inspection via Manifest V3
  - Dynamic toolbar badge indicating page readiness percentage
  - Isolation of IPv4-only dependencies, third-party CDNs, and tracking scripts
  - Apex host vs sub-resource compliance based on SAP Webres6 principles
  - 1-click integration with the AIORI PS-027 4-Stage OSI Diagnostic Auditor

---

## Permissions Justification

| Permission | Technical Requirement & Justification |
| :--- | :--- |
| `webRequest` | Required to read the remote server IP address (`details.ip`) of HTTP/HTTPS requests to determine whether resources were loaded via IPv6 or IPv4. |
| `tabs` | Required to identify the active tab's URL and title and bind captured network traces to the corresponding browser tab. |
| `storage` | Required to persist per-tab diagnostic metrics in `chrome.storage.session` so that telemetry is maintained across service worker idle lifecycles. |
| `activeTab` | Required to provide user-triggered actions when the extension icon is clicked. |
| `host_permissions` (`<all_urls>`) | Required because modern web applications load dependencies (scripts, stylesheets, fonts) from arbitrary third-party domains across the internet. |

---

## Privacy & Data Use Disclosures
- **Data Collection**: None. The extension does not collect, log, or transmit personal data, browsing history, or user identifiers.
- **Data Processing**: All IP address detection occurs locally in-memory within the user's browser session.
- **Remote Communications**: The extension makes zero external tracking requests. Optional "Deep Audit" triggers local/configured diagnostic pipelines on user initiation only.
