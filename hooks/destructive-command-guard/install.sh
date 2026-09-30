#!/usr/bin/env bash
# 2-command installer for Claude Code Destructive Command Guard
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${HOME}/.claude/hooks"

echo "Installing Claude Code PreToolUse guard..."
mkdir -p "${TARGET_DIR}"
cp "${SCRIPT_DIR}/pre-tool-use" "${TARGET_DIR}/pre-tool-use"
chmod +x "${TARGET_DIR}/pre-tool-use"

echo "Installed successfully to ${TARGET_DIR}/pre-tool-use"
echo "Blocked log will be written to ${TARGET_DIR}/blocked.log"
