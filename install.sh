#!/usr/bin/env bash

set -e

HOOK_DIR="$HOME/.claude/hooks"
HOOK_SOURCE="$(cd "$(dirname "$0")" && pwd)/destructive_bash_guard.sh"
HOOK_TARGET="$HOOK_DIR/destructive_bash_guard.sh"
SETTINGS_FILE="$HOME/.claude/settings.json"

if ! command -v jq >/dev/null 2>&1; then
    echo "Error: jq is required. Install jq first."
    exit 1
fi

mkdir -p "$HOOK_DIR"

cp "$HOOK_SOURCE" "$HOOK_TARGET"
chmod +x "$HOOK_TARGET"

if [ -f "$SETTINGS_FILE" ]; then
    SETTINGS="$(cat "$SETTINGS_FILE")"
else
    SETTINGS='{}'
fi

UPDATED="$(printf '%s' "$SETTINGS" | jq \
    --arg hook "$HOOK_TARGET" \
    '
    .hooks = (.hooks // {}) |
    .hooks.PreToolUse = (
        (.hooks.PreToolUse // [])
        | map(
            select(
                .hooks == null
                or all(.hooks[]; .command != $hook)
            )
        )
        + [{
            matcher: "Bash",
            hooks: [{
                type: "command",
                command: $hook,
                timeout: 10
            }]
        }]
    )
    ')"

printf '%s\n' "$UPDATED" > "$SETTINGS_FILE"

echo "Destructive Bash guard installed successfully."
echo "Hook: $HOOK_TARGET"
echo "Settings: $SETTINGS_FILE"
echo "Timeout: 10 seconds"
