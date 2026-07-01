#!/usr/bin/env bash
# One-command installer: copies the hook into ~/.claude/hooks/ and registers it
# as a PreToolUse(Bash) hook in ~/.claude/settings.json (idempotent).
set -euo pipefail

HOOK_SRC="$(cd "$(dirname "$0")" && pwd)/block-destructive.py"
HOOK_DIR="$HOME/.claude/hooks"
SETTINGS="$HOME/.claude/settings.json"

mkdir -p "$HOOK_DIR"
cp "$HOOK_SRC" "$HOOK_DIR/block-destructive.py"
chmod +x "$HOOK_DIR/block-destructive.py"

python3 - "$SETTINGS" <<'PY'
import json, os, sys

path = sys.argv[1]
cmd = "python3 ~/.claude/hooks/block-destructive.py"

settings = {}
if os.path.exists(path):
    try:
        with open(path) as f:
            settings = json.load(f)
    except ValueError:
        print(f"! {path} is not valid JSON — leaving it alone. Add the hook manually (see README).")
        sys.exit(1)

hooks = settings.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])

# already installed? (idempotent)
for entry in pre:
    for h in entry.get("hooks", []):
        if h.get("command") == cmd:
            print("Hook already registered — nothing to do.")
            sys.exit(0)

pre.append({"matcher": "Bash", "hooks": [{"type": "command", "command": cmd}]})

os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w") as f:
    json.dump(settings, f, indent=2)
    f.write("\n")
print(f"Registered PreToolUse(Bash) hook in {path}")
PY

echo "Installed. New Claude Code sessions will block destructive bash commands."
