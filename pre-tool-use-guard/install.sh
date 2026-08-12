#!/usr/bin/env bash
# pre-tool-use-guard installer — 1 command install
set -euo pipefail
HOOKS_DIR="$HOME/.claude/hooks"
SETTINGS="$HOME/.claude/settings.json"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$HOOKS_DIR"
cp "$SCRIPT_DIR/pre_tool_use_guard.py" "$HOOKS_DIR/"

python3 - "$SETTINGS" "$HOOKS_DIR" <<'PY'
import json, sys
settings_path, hooks_dir = sys.argv[1], sys.argv[2]
cmd = f"python3 {hooks_dir}/pre_tool_use_guard.py"

import pathlib
pathlib.Path(settings_path).parent.mkdir(parents=True, exist_ok=True)
if pathlib.Path(settings_path).exists():
    with open(settings_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
else:
    cfg = {}
hooks = cfg.setdefault("hooks", {}).setdefault("PreToolUse", [])
for entry in hooks:
    for h in entry.get("hooks", []):
        if h.get("command", "").strip().endswith("pre_tool_use_guard.py"):
            print("already installed")
            raise SystemExit(0)
hooks.append({"matcher": "Bash", "hooks": [{"type": "command", "command": cmd}]})
with open(settings_path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2)
print("installed")
PY
echo "Done. pre-tool-use-guard is active."
