#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${HOME}/.local/bin"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "${INSTALL_DIR}"
ln -sf "${SCRIPT_DIR}/claude_review.py" "${INSTALL_DIR}/claude-review"
chmod +x "${SCRIPT_DIR}/claude_review.py"

echo "Installed claude-review to ${INSTALL_DIR}/claude-review"
echo "Make sure ${INSTALL_DIR} is on your PATH."
