#!/usr/bin/env bash
# One-command installer for the block-destructive-bash PreToolUse hook.
#
#   bash install.sh
#
# Copies the hook into ~/.claude/hooks/ and merges the PreToolUse entry into
# ~/.claude/settings.json (existing settings are backed up first, never replaced).
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_SRC="$SRC_DIR/block_destructive_bash.py"
HOOK_DEST="$HOME/.claude/hooks/block_destructive_bash.py"
SETTINGS="$HOME/.claude/settings.json"

PY=""
for candidate in python3 python3.12 python3.11 python; do
    if command -v "$candidate" >/dev/null 2>&1 &&
       "$candidate" -c 'import sys; assert sys.version_info >= (3, 7)' >/dev/null 2>&1; then
        PY="$candidate"
        break
    fi
done
if [ -z "$PY" ]; then
    echo "python 3.7+ is required but no working interpreter was found on PATH" >&2
    echo "(Windows note: the Microsoft Store 'python3' stub does not count)" >&2
    exit 1
fi

mkdir -p "$HOME/.claude/hooks"
cp "$HOOK_SRC" "$HOOK_DEST"
chmod +x "$HOOK_DEST" 2>/dev/null || true

"$PY" - "$SETTINGS" "$PY" <<'PY'
import json, os, shutil, sys, time

settings_path = sys.argv[1]
py = sys.argv[2]
hook_cmd = f'{py} "{os.path.expanduser("~/.claude/hooks/block_destructive_bash.py")}"'

data = {}
if os.path.exists(settings_path):
    if os.path.getsize(settings_path) > 0:
        with open(settings_path, encoding="utf-8") as fh:
            data = json.load(fh)
    backup = f"{settings_path}.bak-{time.strftime('%Y%m%d-%H%M%S')}"
    shutil.copy2(settings_path, backup)
    print(f"backed up settings -> {backup}")

hooks = data.setdefault("hooks", {})
pre = hooks.setdefault("PreToolUse", [])

entry = {
    "matcher": "Bash",
    "hooks": [{"type": "command", "command": hook_cmd}],
}

# idempotent: replace an existing entry for this hook, otherwise append
existing = None
for item in pre:
    for h in item.get("hooks", []) or []:
        if "block_destructive_bash.py" in (h.get("command") or ""):
            existing = item
            break
    if existing:
        break

if existing is not None:
    existing["matcher"] = "Bash"
    existing["hooks"] = entry["hooks"]
    print("updated existing PreToolUse entry")
else:
    pre.append(entry)
    print("added PreToolUse entry")

os.makedirs(os.path.dirname(settings_path), exist_ok=True)
with open(settings_path, "w", encoding="utf-8") as fh:
    json.dump(data, fh, indent=2, ensure_ascii=False)
    fh.write("\n")
print(f"wrote {settings_path}")
PY

echo "installed -> $HOOK_DEST (interpreter: $PY)"
echo "verify with: $PY \"$HOOK_DEST\" --check 'rm -rf /'"
