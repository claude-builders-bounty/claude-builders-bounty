#!/usr/bin/env bash
# Install destructive-bash guard into ~/.claude/hooks and register PreToolUse hook.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_SRC="${ROOT}/hooks/block-destructive.sh"
HOOK_DST="${HOME}/.claude/hooks/block-destructive.sh"
SETTINGS="${HOME}/.claude/settings.json"

mkdir -p "${HOME}/.claude/hooks"
install -m 755 "$HOOK_SRC" "$HOOK_DST"
touch "${HOME}/.claude/hooks/blocked.log"
chmod 600 "${HOME}/.claude/hooks/blocked.log" 2>/dev/null || true

if [[ -f "$SETTINGS" ]]; then
  tmp=$(mktemp)
  jq --arg cmd "$HOOK_DST" '
    .hooks //= {} |
    .hooks.PreToolUse //= [] |
    if any(.hooks.PreToolUse[]?; .matcher == "Bash") then
      .hooks.PreToolUse |= map(
        if .matcher == "Bash" then
          .hooks //= [] |
          if any(.hooks[]?; .command == $cmd) then . else .hooks += [{"type": "command", "command": $cmd}] end
        else . end
      )
    else
      .hooks.PreToolUse += [{"matcher": "Bash", "hooks": [{"type": "command", "command": $cmd}]}]
    end
  ' "$SETTINGS" >"$tmp"
  mv "$tmp" "$SETTINGS"
else
  mkdir -p "${HOME}/.claude"
  jq -n --arg cmd "$HOOK_DST" '{
    hooks: {
      PreToolUse: [
        {
          matcher: "Bash",
          hooks: [
            { type: "command", command: $cmd }
          ]
        }
      ]
    }
  }' >"$SETTINGS"
fi

echo "Installed hook to $HOOK_DST"
echo "Registered PreToolUse matcher in $SETTINGS"
