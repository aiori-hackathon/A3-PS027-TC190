# IPv6 Readiness Inspector (Chrome Extension - Manifest V3)

A Chrome extension built for **AIORI-3 PS-027** that provides real-time in-browser inspection of IPv6 reachability across the active webpage and all its sub-resources (scripts, stylesheets, fonts, CDNs, and API calls).

---

## Features
- **Real-Time WebRequest Socket Tracking**: Intercepts active network transactions and determines whether each resource was retrieved over IPv6 or IPv4.
- **Dynamic Action Toolbar Badge**: Displays live readiness percentage (e.g. `85%`, `100%`, `0%`) directly on the extension icon with status colors.
- **Apex Host vs Sub-Resource Isolation**: Implements the official SAP Webres6 principle: if the apex host lacks IPv6, overall readiness is flagged immediately.
- **Host Aggregation List**: Filter by `All`, `IPv4 Only`, or `IPv6`, with instant domain search.
- **1-Click Deep Audit**: Launch the full 4-Stage OSI Gauntlet (DNS, TCP, TLS, HTTP) in the local/cloud auditor dashboard.
- **Clean Minimalist Design**: Follows GitHub Dark/Primer design principles. Zero emojis, zero gradients.

---

## How to Install (Load Unpacked in Chrome / Brave / Edge)

1. Open Google Chrome (or any Chromium browser).
2. Navigate to `chrome://extensions/`.
3. In the top-right corner, toggle **Developer mode** to **ON**.
4. Click the **Load unpacked** button in the top-left corner.
5. Select the `extension/` folder located inside this repository:
   ```
   /Users/apple/Aiori/extension
   ```
6. The **IPv6 Readiness Inspector** icon will appear on your browser toolbar!

---

## How to Test
1. Visit any website (e.g., `https://google.com`, `https://github.com`, or `https://aiori.in`).
2. Click the extension icon in your Chrome toolbar.
3. Observe:
   - The live IPv6 Readiness Score %
   - The Apex IP address (IPv6 or IPv4)
   - Breakdown of all 3rd-party CDNs, fonts, and scripts
   - Click **Launch 4-Stage OSI Deep Audit** to run full diagnostic benchmarks on `http://localhost:8000`.
