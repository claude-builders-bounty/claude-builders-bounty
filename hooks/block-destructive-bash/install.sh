#!/usr/bin/env bash
# Install block-destructive-bash as a Claude Code PreToolUse hook.
# Usage: bash install.sh
set -euo pipefail

HOOKS_DIR="$HOME/.claude/hooks"
SETTINGS="$HOME/.claude/settings.json"
SRC="$(cd "$(dirname "$0")" && pwd)/block_destructive_bash.py"
DEST="$HOOKS_DIR/block_destructive_bash.py"

mkdir -p "$HOOKS_DIR"
cp "$SRC" "$DEST"
chmod +x "$DEST"

python3 - "$SETTINGS" "$DEST" <<'PY'
import json, sys, os, pathlib
settings_path, hook_path = sys.argv[1], sys.argv[2]
p = pathlib.Path(settings_path)
data = {}
if p.exists():
    try: data = json.loads(p.read_text())
    except Exception: data = {}
hooks = data.setdefault("hooks", {})
pretool = hooks.setdefault("PreToolUse", [])
entry = {
    "matcher": "Bash",
    "hooks": [{"type": "command", "command": f"python3 {hook_path}"}],
}
# de-dupe
if not any(
    isinstance(e, dict) and e.get("matcher") == "Bash"
    and any(h.get("command", "").endswith("block_destructive_bash.py")
            for h in e.get("hooks", []))
    for e in pretool
):
    pretool.append(entry)
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(data, indent=2))
print(f"Installed hook → {hook_path}")
print(f"Registered in   → {settings_path}")
PY
