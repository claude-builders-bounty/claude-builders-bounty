#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DEST="${HOME}/.claude/hooks"
mkdir -p "$DEST"
cp "$HERE/block-destructive.py" "$DEST/block-destructive.py"
chmod +x "$DEST/block-destructive.py"
touch "$DEST/blocked.log"
python3 - << 'INNER'
import json
from pathlib import Path
settings = Path.home() / ".claude" / "settings.json"
settings.parent.mkdir(parents=True, exist_ok=True)
data = {}
if settings.exists():
    try:
        data = json.loads(settings.read_text() or "{}")
    except json.JSONDecodeError:
        data = {}
hooks = data.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])
entry = {
    "matcher": "Bash",
    "hooks": [{
        "type": "command",
        "command": str(Path.home() / ".claude/hooks/block-destructive.py"),
    }],
}
def is_ours(item):
    try:
        cmd = item.get("hooks", [{}])[0].get("command", "")
    except Exception:
        cmd = ""
    return "block-destructive.py" in str(cmd)
pre[:] = [p for p in pre if not is_ours(p)]
pre.append(entry)
settings.write_text(json.dumps(data, indent=2) + "\n")
print("Installed hook and updated", settings)
INNER
echo "Blocked attempts log: ${DEST}/blocked.log"
