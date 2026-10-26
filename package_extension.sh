#!/bin/bash
# package_extension.sh — Packages clean extension ZIP for Chrome Web Store & GitHub Releases

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_ZIP="${SCRIPT_DIR}/extension.zip"

echo "Packaging extension..."
rm -f "$OUTPUT_ZIP"

cd "${SCRIPT_DIR}/extension"
zip -r "$OUTPUT_ZIP" manifest.json background.js sidepanel.html sidepanel.js sidepanel.css icons -x "*.DS_Store*"

echo "Successfully built ${OUTPUT_ZIP} ($(du -h "$OUTPUT_ZIP" | cut -f1))"
