#!/usr/bin/env bash
# Installs the guard hook into ~/.claude/settings.json (user-wide) so every
# project gets it. Safe to re-run: it replaces our own entry and leaves
# unrelated settings untouched.
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_DIR="$HOME/.claude/hooks"
SETTINGS="$HOME/.claude/settings.json"
TARGET="$HOOKS_DIR/block_bash.py"

mkdir -p "$HOOKS_DIR"
cp "$SRC_DIR/block_bash.py" "$TARGET"
chmod +x "$TARGET"
[ -f "$SETTINGS" ] || echo '{}' > "$SETTINGS"

python3 - "$SETTINGS" <<'PY'
import json, sys

path = sys.argv[1]
with open(path, encoding="utf-8") as fh:
    try:
        cfg = json.load(fh)
    except json.JSONDecodeError:
        cfg = {}

hooks = cfg.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])
entry = {
    "matcher": "Bash",
    "hooks": [
        {"type": "command", "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block_bash.py"}
    ],
}

# Replace an existing copy of this hook, keep everything else.
kept = [e for e in pre
        if not any("block_bash.py" in h.get("command", "")
                   for h in (e.get("hooks") or []))]
kept.append(entry)
hooks["PreToolUse"] = kept

with open(path, "w", encoding="utf-8") as fh:
    json.dump(cfg, fh, indent=2)
    fh.write("\n")
print(f"registered PreToolUse(Bash) hook in {path}")
PY

echo "installed: $TARGET"
echo "log file:  $HOOKS_DIR/blocked.log"
