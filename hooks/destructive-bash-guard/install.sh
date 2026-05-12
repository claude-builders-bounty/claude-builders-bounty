#!/usr/bin/env bash
set -euo pipefail

HOOKS_DIR="$HOME/.claude/hooks"
SETTINGS="$HOME/.claude/settings.json"
HOOK_SCRIPT="$HOOKS_DIR/destructive-bash-guard.py"

mkdir -p "$HOOKS_DIR"
cp "$(dirname "$0")/hook.py" "$HOOK_SCRIPT"
chmod +x "$HOOK_SCRIPT"

# Merge hook config into settings.json using Python
python3 - "$SETTINGS" "$HOOK_SCRIPT" <<'EOF'
import json, sys
from pathlib import Path

settings_path = Path(sys.argv[1])
hook_script = sys.argv[2]

settings = {}
if settings_path.exists():
    try:
        settings = json.loads(settings_path.read_text())
    except json.JSONDecodeError:
        pass

hooks = settings.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])

entry = {
    "matcher": "Bash",
    "hooks": [{"type": "command", "command": hook_script}]
}

# Avoid duplicates
already = any(
    h.get("hooks", [{}])[0].get("command") == hook_script
    for h in pre
    if h.get("matcher") == "Bash"
)
if not already:
    pre.append(entry)

settings_path.parent.mkdir(parents=True, exist_ok=True)
settings_path.write_text(json.dumps(settings, indent=2) + "\n")
print(f"Hook registered in {settings_path}")
EOF

echo "✅ destructive-bash-guard installed to $HOOK_SCRIPT"
echo "   Logs: $HOOKS_DIR/blocked.log"
