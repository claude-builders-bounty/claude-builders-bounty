#!/usr/bin/env bash
# Install pretooluse_bash_guard as a Claude Code PreToolUse hook.
# Merges into ~/.claude/settings.json (backs up the original first) and
# copies the hook script to ~/.claude/hooks/pretooluse_bash_guard.py.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_DIR="$HOME/.claude/hooks"
HOOK_PATH="$HOOK_DIR/pretooluse_bash_guard.py"
SETTINGS="$HOME/.claude/settings.json"

mkdir -p "$HOOK_DIR"
cp "$SCRIPT_DIR/pretooluse_bash_guard.py" "$HOOK_PATH"
chmod +x "$HOOK_PATH"

if [ -f "$SETTINGS" ]; then
  cp "$SETTINGS" "$SETTINGS.bak.$(date +%s)"
  python3 - "$SETTINGS" "$HOOK_PATH" <<'PYEOF'
import json, sys
path, hook = sys.argv[1], sys.argv[2]
cfg = json.load(open(path))
pre = cfg.setdefault("hooks", {}).setdefault("PreToolUse", [])
entry = {"matcher": "Bash", "hooks": [{"type": "command", "command": f"python3 {hook}"}]}
def has(e):
    return e.get("matcher") == "Bash" and any(
        str(h.get("command", "")).endswith("pretooluse_bash_guard.py") for h in e.get("hooks", []))
if not any(has(e) for e in pre):
    pre.append(entry)
    json.dump(cfg, open(path, "w"), indent=2)
    print("settings.json updated (original backed up)")
else:
    print("settings.json already configured (original backed up)")
PYEOF
else
  mkdir -p "$HOME/.claude"
  python3 - "$SETTINGS" "$HOOK_PATH" <<'PYEOF'
import json, sys
path, hook = sys.argv[1], sys.argv[2]
cfg = {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": f"python3 {hook}"}]}]}}
json.dump(cfg, open(path, "w"), indent=2)
print("settings.json created")
PYEOF
fi

echo "Installed: destructive bash commands are now blocked and logged to $HOOK_DIR/blocked.log"
