#!/usr/bin/env bash
set -euo pipefail

REPO="cheneeheng/claude-code-plugin-toggler"
TARGET_DIR="/tmp/vsix"

mkdir -p "$TARGET_DIR"

echo "Fetching latest VSIX from $REPO..."
if ! gh release download --repo "$REPO" --pattern "*.vsix" --dir "$TARGET_DIR"; then
    echo "Warning: Unable to download VSIX from latest release. Skipping installation."
    exit 0
fi

VSIX_FILE=$(ls "$TARGET_DIR"/*.vsix 2>/dev/null | head -n 1 || true)

if [ -z "${VSIX_FILE:-}" ]; then
    echo "Warning: No VSIX asset found in latest release. Skipping installation."
    exit 0
fi

echo "Locating VS Code server CLI..."
VSCODE_SERVER=$(find /vscode/vscode-server/bin -type f -name code-server | head -n 1 || true)

if [ -z "${VSCODE_SERVER:-}" ]; then
    echo "Warning: VS Code server CLI not found. Skipping VSIX installation."
    exit 0
fi

echo "Using VS Code server CLI: $VSCODE_SERVER"
"$VSCODE_SERVER" --install-extension "$VSIX_FILE" --force || \
    echo "Warning: VSIX installation failed. Continuing."

echo "VSIX installation completed."
