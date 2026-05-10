#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_DIR="${HOME}/.claude/hooks"
TARGET="${HOOK_DIR}/destructive_bash_guard.py"

mkdir -p "${HOOK_DIR}"
cp "${SCRIPT_DIR}/destructive_bash_guard.py" "${TARGET}"
chmod +x "${TARGET}"
python3 "${TARGET}" --install-settings

echo "Installed destructive Bash guard at ${TARGET}"
