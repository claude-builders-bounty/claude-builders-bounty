#!/usr/bin/env bash
# install.sh -- installs block-destructive-bash.py as a Claude Code
# PreToolUse hook and registers it in ~/.claude/settings.json.
#
# Usage:  bash install.sh
# Idempotent: running it twice does not duplicate the hook registration.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_SRC="$SCRIPT_DIR/block-destructive-bash.py"
SETTINGS_SRC="$SCRIPT_DIR/settings.json"
HOOK_DIR="$HOME/.claude/hooks"
HOOK_DEST="$HOOK_DIR/block-destructive-bash.py"
SETTINGS_DEST="$HOME/.claude/settings.json"

mkdir -p "$HOOK_DIR"
cp "$HOOK_SRC" "$HOOK_DEST"
chmod +x "$HOOK_DEST"

python3 - "$SETTINGS_SRC" "$SETTINGS_DEST" <<'PYEOF'
import json
import sys

src_path, dest_path = sys.argv[1], sys.argv[2]
with open(src_path, encoding="utf-8") as f:
    snippet = json.load(f)

try:
    with open(dest_path, encoding="utf-8") as f:
        settings = json.load(f)
except FileNotFoundError:
    settings = {}
except json.JSONDecodeError as exc:
    print(f"ERROR: {dest_path} is not valid JSON: {exc}", file=sys.stderr)
    print("Fix or move that file, then run install.sh again.", file=sys.stderr)
    sys.exit(1)

hooks = settings.setdefault("hooks", {})
pre_tool_use = hooks.setdefault("PreToolUse", [])
new_entry = snippet["hooks"]["PreToolUse"][0]
new_command = new_entry["hooks"][0]["command"]

already = any(
    isinstance(entry, dict)
    and entry.get("hooks")
    and entry["hooks"][0].get("command") == new_command
    for entry in pre_tool_use
)
if not already:
    pre_tool_use.append(new_entry)

with open(dest_path, "w", encoding="utf-8") as f:
    json.dump(settings, f, indent=2)
    f.write("\n")
PYEOF

echo "Installed hook: $HOOK_DEST"
echo "Registered in:  $SETTINGS_DEST"
echo "Blocked attempts will be logged to ~/.claude/hooks/blocked.log"
