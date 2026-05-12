#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if command -v python3 >/dev/null 2>&1; then
  python3 "$SCRIPT_DIR/install.py"
else
  python "$SCRIPT_DIR/install.py"
fi
