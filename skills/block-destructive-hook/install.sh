#!/bin/bash
# Install and register the hook without replacing unrelated Claude settings.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
DEST="${HOME:?}/.claude/hooks"
HOOK="$DEST/block-destructive.sh"
mkdir -p "$DEST"
install -m 700 "$SCRIPT_DIR/block-destructive.sh" "$HOOK"
install -m 700 "$SCRIPT_DIR/command_parser.py" "$DEST/command_parser.py"
SETTINGS="$HOME/.claude/settings.json"
python3 - "$SETTINGS" "$HOOK" <<'PY'
import json, os, sys, tempfile
settings_path, hook = sys.argv[1:]
try:
    with open(settings_path) as f:
        settings = json.load(f)
except FileNotFoundError:
    settings = {}
except json.JSONDecodeError as e:
    raise SystemExit(f"Cannot update invalid JSON in {settings_path}: {e}")

hooks = settings.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])
entry = {"matcher": "Bash", "hooks": [{"type": "command", "command": hook, "timeout": 10}]}
if not any(item == entry for item in pre if isinstance(item, dict)):
    pre.append(entry)
os.makedirs(os.path.dirname(settings_path), exist_ok=True)
fd, tmp = tempfile.mkstemp(prefix="settings.", suffix=".json", dir=os.path.dirname(settings_path) or ".")
try:
    with os.fdopen(fd, "w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")
    os.replace(tmp, settings_path)
finally:
    if os.path.exists(tmp): os.unlink(tmp)
PY
printf 'Installed and registered %s\n' "$HOOK"
