#!/usr/bin/env bash
# Install the destructive-command PreToolUse hook into ~/.claude/
# Idempotent. Requires: bash, python3, optionally python3 for JSON merge.
set -euo pipefail

SRC_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
HOOK_DIR="${HOME}/.claude/hooks"
SETTINGS="${HOME}/.claude/settings.json"
HOOK_DST="${HOOK_DIR}/block-destructive.sh"
PY_DST="${HOOK_DIR}/block_destructive.py"

mkdir -p "$HOOK_DIR" "${HOME}/.claude"

cp -f "$SRC_DIR/block_destructive.py" "$PY_DST"
cp -f "$SRC_DIR/block-destructive.sh" "$HOOK_DST"
# Rewrite launcher to always call the installed Python next to it
cat > "$HOOK_DST" << 'LAUNCH'
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/block_destructive.py"
LAUNCH
chmod +x "$HOOK_DST" "$PY_DST"

# Merge PreToolUse entry into settings.json without wiping other hooks
python3 - <<'PY'
import json, os, shutil
from pathlib import Path

settings_path = Path.home() / ".claude" / "settings.json"
hook_cmd = str(Path.home() / ".claude" / "hooks" / "block-destructive.sh")
entry = {
    "matcher": "Bash",
    "hooks": [{"type": "command", "command": hook_cmd}],
}

if settings_path.exists():
    shutil.copy2(settings_path, settings_path.with_suffix(".json.bak"))
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8") or "{}")
    except json.JSONDecodeError:
        data = {}
else:
    data = {}

hooks = data.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])

# Remove prior installs of this exact command, then append
def is_ours(group):
    for h in group.get("hooks") or []:
        cmd = h.get("command") or ""
        if "block-destructive" in cmd or "block_destructive" in cmd:
            return True
    return False

pre[:] = [g for g in pre if not is_ours(g)]
pre.append(entry)
settings_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print(f"Installed hook → {hook_cmd}")
print(f"Updated settings → {settings_path} (backup .bak if previous existed)")
PY

# Quick self-check
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/x"},"cwd":"/tmp"}' \
  | python3 "$PY_DST" >/tmp/block-destructive-selftest.out 2>/tmp/block-destructive-selftest.err || true
if grep -q '"permissionDecision": "deny"' /tmp/block-destructive-selftest.out 2>/dev/null \
   || grep -q 'permissionDecision' /tmp/block-destructive-selftest.out 2>/dev/null; then
  echo "Self-test: OK (rm -rf denied)"
else
  echo "Self-test: unexpected output — check /tmp/block-destructive-selftest.out" >&2
  cat /tmp/block-destructive-selftest.out >&2 || true
fi

echo "Done. Restart Claude Code (or open a new session) so the hook is picked up."
