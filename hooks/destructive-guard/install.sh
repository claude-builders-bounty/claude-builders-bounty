#!/usr/bin/env bash
# Install or uninstall destructive-guard in Claude Code hooks.
set -euo pipefail

HOOK_DIR="$HOME/.claude/hooks"
HOOK_SRC="$(cd "$(dirname "$0")" && pwd)/hook.py"
HOOK_DEST="$HOOK_DIR/destructive-guard.py"
SETTINGS="$HOME/.claude/settings.json"

if [ "${1:-}" = "--uninstall" ]; then
    rm -f "$HOOK_DEST"
    python3 - "$SETTINGS" <<'PYEOF'
import json, sys
from pathlib import Path
settings_path = Path(sys.argv[1])
if not settings_path.exists():
    sys.exit(0)
cfg = json.loads(settings_path.read_text())
pre = cfg.get("hooks", {}).get("PreToolUse", [])
cfg["hooks"]["PreToolUse"] = [
    h for h in pre
    if not (h.get("matcher") == "Bash" and
            any("destructive-guard" in str(c.get("command", "")) for c in h.get("hooks", [])))
]
settings_path.write_text(json.dumps(cfg, indent=2) + "\n")
PYEOF
    echo "destructive-guard uninstalled."
    exit 0
fi

mkdir -p "$HOOK_DIR"
cp "$HOOK_SRC" "$HOOK_DEST"
chmod +x "$HOOK_DEST"

python3 - "$HOOK_DEST" "$SETTINGS" <<'PYEOF'
import json, sys
from pathlib import Path

hook_path, settings_path = sys.argv[1], Path(sys.argv[2])
cfg = json.loads(settings_path.read_text()) if settings_path.exists() else {}
pre = cfg.setdefault("hooks", {}).setdefault("PreToolUse", [])
entry = {"matcher": "Bash", "hooks": [{"type": "command", "command": f"python3 {hook_path}"}]}
already = any(
    h.get("matcher") == "Bash" and
    any("destructive-guard" in str(c.get("command", "")) for c in h.get("hooks", []))
    for h in pre
)
if not already:
    pre.append(entry)
settings_path.write_text(json.dumps(cfg, indent=2) + "\n")
PYEOF

echo "destructive-guard installed at $HOOK_DEST"
echo "Blocking: rm -rf | DROP TABLE | TRUNCATE | DELETE FROM (no WHERE) | git push --force | dd of=/dev/* | fork bombs"
echo "Log: ~/.claude/hooks/blocked.log"
echo "To uninstall: bash $(basename "$0") --uninstall"
