#!/usr/bin/env bash
# Install destructive-command PreToolUse hook into ~/.claude/
# Usage: bash install.sh
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_SRC="$SRC_DIR/hooks/block-destructive.py"
DEST_DIR="${HOME}/.claude/hooks"
SETTINGS="${HOME}/.claude/settings.json"

mkdir -p "$DEST_DIR"
cp "$HOOK_SRC" "$DEST_DIR/block-destructive.py"
chmod +x "$DEST_DIR/block-destructive.py"
touch "$DEST_DIR/blocked.log"

python3 - <<'PY'
import json, os
from pathlib import Path

settings_path = Path.home() / ".claude" / "settings.json"
settings_path.parent.mkdir(parents=True, exist_ok=True)

hook_entry = {
    "type": "command",
    "command": 'python3 "$HOME/.claude/hooks/block-destructive.py"',
    "timeout": 10,
}
matcher_block = {"matcher": "Bash", "hooks": [hook_entry]}

if settings_path.exists() and settings_path.stat().st_size > 0:
    data = json.loads(settings_path.read_text(encoding="utf-8"))
else:
    data = {}

hooks = data.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])

# Idempotent: remove prior installs of this hook, then append
def is_ours(h):
    cmd = (h.get("command") or "") if isinstance(h, dict) else ""
    return "block-destructive.py" in cmd

new_pre = []
for block in pre:
    if not isinstance(block, dict):
        new_pre.append(block)
        continue
    inner = [h for h in block.get("hooks", []) if not is_ours(h)]
    if block.get("matcher") == "Bash":
        inner.append(hook_entry)
        block = {**block, "hooks": inner}
        new_pre.append(block)
    else:
        if inner:
            new_pre.append({**block, "hooks": inner})
        else:
            new_pre.append(block)

# Ensure a Bash matcher exists
if not any(isinstance(b, dict) and b.get("matcher") == "Bash" for b in new_pre):
    new_pre.append(matcher_block)

hooks["PreToolUse"] = new_pre
settings_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print(f"Updated {settings_path}")
PY

echo "Installed: $DEST_DIR/block-destructive.py"
echo "Log file:  $DEST_DIR/blocked.log"
echo "Done. Restart Claude Code (or wait for settings reload), then try a destructive command."
