#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_DIR="$HOME/.claude/hooks"
SETTINGS_FILE="$HOME/.claude/settings.json"
HOOK_SOURCE="$REPO_DIR/hooks/destructive-bash-guard.py"
HOOK_TARGET="$HOOK_DIR/destructive-bash-guard.py"

mkdir -p "$HOOK_DIR"
cp "$HOOK_SOURCE" "$HOOK_TARGET"
chmod +x "$HOOK_TARGET"

python3 - "$SETTINGS_FILE" "$HOOK_TARGET" <<'PY'
import json
import sys
from pathlib import Path

settings_path = Path(sys.argv[1]).expanduser()
hook_path = Path(sys.argv[2]).expanduser()
settings_path.parent.mkdir(parents=True, exist_ok=True)

if settings_path.exists() and settings_path.read_text().strip():
    data = json.loads(settings_path.read_text())
else:
    data = {}

hooks = data.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])
entry = {
    "matcher": "Bash",
    "hooks": [
        {
            "type": "command",
            "command": str(hook_path),
        }
    ],
}

# Avoid duplicate installer entries.
needle = str(hook_path)
for existing in pre:
    for hook in existing.get("hooks", []) if isinstance(existing, dict) else []:
        if hook.get("command") == needle:
            break
    else:
        continue
    break
else:
    pre.append(entry)

settings_path.write_text(json.dumps(data, indent=2) + "\n")
PY

echo "Installed destructive-bash-guard at $HOOK_TARGET"
echo "Updated Claude Code settings at $SETTINGS_FILE"
echo "Blocked attempts will be logged to $HOOK_DIR/blocked.log"
