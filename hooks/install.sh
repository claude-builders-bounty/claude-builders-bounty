#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${HOME}/.claude/hooks"
TARGET="${TARGET_DIR}/block_destructive_bash.py"

mkdir -p "${TARGET_DIR}"
cp "${SOURCE_DIR}/block_destructive_bash.py" "${TARGET}"
chmod +x "${TARGET}"

echo "Installed ${TARGET}"
echo "Add the hooks/README.md settings.json snippet to ~/.claude/settings.json."
