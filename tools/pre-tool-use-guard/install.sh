#!/usr/bin/env bash
set -euo pipefail

if ! command -v jq &>/dev/null; then
  echo "ERROR: jq is required but not installed." >&2
  echo "  macOS:  brew install jq" >&2
  echo "  Linux:  sudo apt-get install jq" >&2
  exit 1
fi

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
HOOKS_DIR="${HOME}/.claude/hooks"
SETTINGS="${HOME}/.claude/settings.json"
HOOK_DEST="${HOOKS_DIR}/block-destructive.sh"

mkdir -p "$HOOKS_DIR"
cp "$SCRIPT_DIR/block-destructive.sh" "$HOOK_DEST"
chmod +x "$HOOK_DEST"

if [[ ! -f "$SETTINGS" ]]; then
  echo '{}' > "$SETTINGS"
fi

if ! jq empty "$SETTINGS" 2>/dev/null; then
  echo "ERROR: $SETTINGS contains invalid JSON." >&2
  echo "  Fix it manually (run: jq . \"$SETTINGS\" to see the error) then re-run this installer." >&2
  exit 1
fi

HOOK_ENTRY=$(jq -n --arg cmd "$HOOK_DEST" '{
  matcher: "Bash",
  hooks: [{type: "command", command: $cmd, timeout: 10}]
}')

UPDATED=$(jq --argjson entry "$HOOK_ENTRY" '
  .hooks //= {} |
  .hooks.PreToolUse //= [] |
  if (.hooks.PreToolUse | map(select(.hooks[0].command == $entry.hooks[0].command)) | length) > 0
  then .
  else .hooks.PreToolUse = [$entry] + .hooks.PreToolUse
  end
' "$SETTINGS")

if [[ -z "$UPDATED" ]] || ! printf '%s' "$UPDATED" | jq empty 2>/dev/null; then
  echo "ERROR: Failed to produce valid settings JSON. $SETTINGS was NOT modified." >&2
  exit 1
fi

# Atomic write: temp file then rename
TMPFILE=$(mktemp "${SETTINGS}.XXXXXX")
printf '%s\n' "$UPDATED" > "$TMPFILE"
mv "$TMPFILE" "$SETTINGS"

echo "Installed: $HOOK_DEST"
echo "Settings:  $SETTINGS"
echo "Log file:  ${HOOKS_DIR}/blocked.log"
echo ""
echo "Done. The hook is now active for all Claude Code sessions."
