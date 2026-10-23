#!/usr/bin/env bash
# Install the PreToolUse destructive-command hook for Claude Code.
# Usage: curl -fsSL https://raw.githubusercontent.com/1132dadf/claude-builders-bounty/1132dadf-patch-1/hooks/install.sh | bash
set -euo pipefail

RAW_BASE="https://raw.githubusercontent.com/1132dadf/claude-builders-bounty/1132dadf-patch-1/hooks"
HOOK_DIR="${HOME}/.claude/hooks"
HOOK_PATH="${HOOK_DIR}/pre-tool-use.sh"
SETTINGS="${HOME}/.claude/settings.json"

mkdir -p "$HOOK_DIR"
curl -fsSL "${RAW_BASE}/pre-tool-use.sh" -o "$HOOK_PATH"
chmod +x "$HOOK_PATH"

# Register the hook in ~/.claude/settings.json. Prefer python3 (present on
# macOS and most Linux distros), fall back to python, then jq. If none of them
# is available we still install the script and print the snippet to add by hand.
register_with_python() {
  "$1" - "$SETTINGS" "$HOOK_PATH" <<'PY'
import json
import os
import sys

settings_path, hook_path = sys.argv[1], sys.argv[2]
os.makedirs(os.path.dirname(settings_path), exist_ok=True)
try:
    with open(settings_path, encoding="utf-8") as fh:
        data = json.load(fh)
except FileNotFoundError:
    data = {}
except json.JSONDecodeError:
    sys.exit("settings.json exists but is not valid JSON; add the PreToolUse entry manually")

pre = data.setdefault("hooks", {}).setdefault("PreToolUse", [])
already = any(
    hook.get("command") == hook_path
    for group in pre
    for hook in group.get("hooks", [])
)
if not already:
    pre.append({"matcher": "Bash", "hooks": [{"type": "command", "command": hook_path}]})
    with open(settings_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")
print("registered %s for Bash in %s" % (hook_path, settings_path))
PY
}

if command -v python3 >/dev/null 2>&1 && python3 -c 'pass' >/dev/null 2>&1; then
  register_with_python python3
elif command -v python >/dev/null 2>&1 && python -c 'pass' >/dev/null 2>&1; then
  register_with_python python
elif command -v jq >/dev/null 2>&1; then
  mkdir -p "$(dirname "$SETTINGS")"
  if [[ ! -f "$SETTINGS" ]]; then
    printf '{}\n' > "$SETTINGS"
  fi
  tmp=$(mktemp)
  jq --arg hook "$HOOK_PATH" \
    '.hooks.PreToolUse = ((.hooks.PreToolUse // []) + [{"matcher":"Bash","hooks":[{"type":"command","command":$hook}]}])' \
    "$SETTINGS" > "$tmp" && mv "$tmp" "$SETTINGS"
  echo "registered $HOOK_PATH for Bash in $SETTINGS"
else
  cat <<EOF
Installed $HOOK_PATH but could not edit $SETTINGS automatically.
Add this entry to $SETTINGS:

{
  "hooks": {
    "PreToolUse": [
      {"matcher": "Bash", "hooks": [{"type": "command", "command": "$HOOK_PATH"}]}
    ]
  }
}
EOF
fi

echo "Done. Restart Claude Code to load the hook."
