# IPv6 Readiness Auditor - Side Panel Design System

## Overview
A calm, minimal, high-density engineering interface adhering to GitHub Primer and Linear design principles for Chrome Side Panel viewports (320px–480px).

## Color Tokens
- Background Page: `#0d1117`
- Surface Card: `#161b22`
- Surface Subdued: `#0e1319`
- Surface Hover: `#21262d`
- Border Default: `#30363d`
- Border Muted: `#21262d`
- Text Primary: `#e6edf3`
- Text Muted: `#8b949e`
- Text Dim: `#6e7681`
- Focus Outline: `#58a6ff` (2px solid)

### Semantic Protocol States (Always paired with text or icon)
- IPv6 Ready / Pass: `#3fb950`
- IPv4 Only / Fail: `#f85149`
- Broken Route / Timeout: `#d29922`
- Apex Root / Info: `#58a6ff`

## Typography Scale
- Font Family UI: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif
- Font Family Data: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace
- Weights: 400, 500, 600
- 28px / 1.15 (Hero Metric Score, weight 600)
- 20px / 1.25 (Section Titles, weight 600)
- 14px / 1.3  (Subheadings & Prominent Labels, weight 600)
- 13px / 1.4  (Default UI Body & Form Controls, weight 400 & 500)
- 12px / 1.4  (Secondary Meta, Tables & Stepper Titles, weight 500)
- 11px / 1.3  (Badges, Protocol Tags & Microcopy, weight 500)

## Spacing Scale
Strict 6-point scale:
- `4px`  (Micro gaps, inline badges, icon padding)
- `8px`  (Tight stack, button padding, grid gaps)
- `12px` (Card padding, form row spacing)
- `16px` (Section gaps, container margins)
- `24px` (Major panel dividers)
- `32px` (Empty states & hero padding)

## Corner Radii
- `6px`: Cards, input fields, buttons, stepper blocks, tables
- `999px`: Status pills and tag badges only

## Iconography Standard
- 1.5px stroke width SVGs
- Two standard sizes: 16px and 20px
