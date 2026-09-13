#!/usr/bin/env bash
# Install safeguard hook in ≤2 commands (this script is command 1; optional merge is command 2).
set -euo pipefail
DEST="${HOME}/.claude/hooks"
mkdir -p "$DEST"
cp "$(dirname "$0")/hooks/block_destructive.py" "$DEST/block_destructive.py"
chmod +x "$DEST/block_destructive.py"
echo "Installed $DEST/block_destructive.py"
echo "Merge hooks/settings.fragment.json into ~/.claude/settings.json (or run: python3 - <<'PY'"
echo "See README — one jq merge command)."
