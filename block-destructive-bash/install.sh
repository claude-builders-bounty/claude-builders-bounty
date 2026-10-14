#!/usr/bin/env bash
# install.sh — one-command install of the destructive-bash block hook.
# Copies the hook to ~/.claude/hooks/ and registers it in ~/.claude/settings.json
# (idempotent: re-running is safe).
set -euo pipefail

HOOK_SRC="$(dirname "$0")/block-destructive-bash.sh"
HOOK_DST="$HOME/.claude/hooks/block-destructive-bash.sh"
SETTINGS="$HOME/.claude/settings.json"
HOOK_CMD="bash $HOOK_DST"

mkdir -p "$HOME/.claude/hooks"
cp "$HOOK_SRC" "$HOOK_DST"
chmod +x "$HOOK_DST"
echo "installed: $HOOK_DST"

python3 - "$SETTINGS" "$HOOK_CMD" <<'PY'
import json, os, sys

settings_path, hook_cmd = sys.argv[1], sys.argv[2]

if os.path.exists(settings_path):
    with open(settings_path) as f:
        cfg = json.load(f)
else:
    cfg = {}

hooks = cfg.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])

entry = {
    "matcher": "Bash",
    "hooks": [{"type": "command", "command": hook_cmd}],
}

already = any(
    any(h.get("command") == hook_cmd for h in (e.get("hooks") or []))
    for e in pre
)
if already:
    print("already registered in settings.json — nothing to do")
else:
    pre.append(entry)
    print("registered PreToolUse hook in settings.json")

with open(settings_path, "w") as f:
    json.dump(cfg, f, indent=2)
    f.write("\n")
PY

echo
echo "Done. Restart Claude Code for the hook to take effect."
echo "Blocked attempts are logged to ~/.claude/hooks/blocked.log (JSON lines)."
