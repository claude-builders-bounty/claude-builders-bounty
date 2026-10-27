#!/usr/bin/env bash
# Claude Code PreToolUse Hook wrapper for blocking destructive bash commands.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "${SCRIPT_DIR}/block-destructive-bash.py" "$@"
