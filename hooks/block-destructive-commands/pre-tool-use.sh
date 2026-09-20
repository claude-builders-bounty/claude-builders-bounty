#!/usr/bin/env bash
set -eo pipefail

# Claude Code pre-tool-use shell runner
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if command -v python3 &>/dev/null; then
    exec python3 "${SCRIPT_DIR}/pre-tool-use.py" "$@"
elif command -v python &>/dev/null; then
    exec python "${SCRIPT_DIR}/pre-tool-use.py" "$@"
else
    echo "[Hook Error] Python 3 is required for pre-tool-use security hook." >&2
    exit 1
fi
