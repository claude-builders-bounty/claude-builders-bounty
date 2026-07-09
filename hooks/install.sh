#!/usr/bin/env bash
# Install the block-destructive-bash PreToolUse hook into Claude Code.
set -euo pipefail

hooks_dir="${CLAUDE_HOOKS_DIR:-$HOME/.claude/hooks}"
settings="${CLAUDE_SETTINGS:-$HOME/.claude/settings.json}"
src="$(cd "$(dirname "$0")/.." && pwd)/.claude/hooks/block_destructive_bash.py"

mkdir -p "$hooks_dir"
cp "$src" "$hooks_dir/block_destructive_bash.py"
chmod +x "$hooks_dir/block_destructive_bash.py" 2>/dev/null || true

python3 - "$settings" "$hooks_dir/block_destructive_bash.py" <<'PY'
import json, os, sys
settings_path, hook_path = sys.argv[1], sys.argv[2]
os.makedirs(os.path.dirname(settings_path), exist_ok=True)
try:
    with open(settings_path, encoding="utf-8") as fh:
        cfg = json.load(fh)
    if not isinstance(cfg, dict):
        cfg = {}
except (OSError, ValueError):
    cfg = {}
pre = cfg.setdefault("hooks", {}).setdefault("PreToolUse", [])
already = any("block_destructive_bash" in h.get("command", "")
             for m in pre for h in m.get("hooks", []))
if not already:
    pre.append({"matcher": "Bash",
                "hooks": [{"type": "command", "command": f'python3 "{hook_path}"'}]})
    with open(settings_path, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2)
    print(f"registered PreToolUse(Bash) hook in {settings_path}")
else:
    print("hook already registered")
PY

echo "Installed. Destructive bash commands are now blocked in Claude Code."
