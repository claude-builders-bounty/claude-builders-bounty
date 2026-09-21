#!/usr/bin/env bash
# Install block-destructive PreToolUse hook into ~/.claude/
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "${HOME}/.claude/hooks"
cp "${ROOT}/block_destructive.py" "${HOME}/.claude/hooks/block_destructive.py"
chmod +x "${HOME}/.claude/hooks/block_destructive.py"
# Merge or write settings: if no settings.json, copy ours; else print merge hint
SETTINGS="${HOME}/.claude/settings.json"
if [[ ! -f "$SETTINGS" ]]; then
  cp "${ROOT}/settings.json" "$SETTINGS"
  # Expand ${HOME} literally for Claude (settings don't expand HOME in args the same way)
  python3 - <<'PY'
import json, os
from pathlib import Path
p = Path.home() / ".claude" / "settings.json"
data = json.loads(p.read_text())
hook = data["hooks"]["PreToolUse"][0]["hooks"][0]
hook["args"] = [str(Path.home() / ".claude" / "hooks" / "block_destructive.py")]
hook["command"] = "python3"
p.write_text(json.dumps(data, indent=2) + "\n")
print(f"Wrote {p}")
PY
else
  DEST="${HOME}/.claude/hooks/block_destructive.py"
  echo "Hook script installed at: $DEST"
  echo "Merge the PreToolUse entry from $ROOT/settings.json into $SETTINGS"
  echo "Use absolute path: $DEST"
fi
echo "Done. Blocked attempts append to ~/.claude/hooks/blocked.log"
