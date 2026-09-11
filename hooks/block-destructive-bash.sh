#!/usr/bin/env bash
# Claude Code pre-tool-use style guard: block destructive bash patterns.
# Usage: echo "$TOOL_INPUT_JSON" | bash hooks/block-destructive-bash.sh
# Exit 0 = allow, exit 2 = block (stderr reason).
set -euo pipefail

input=$(cat || true)
# Accept raw command string or JSON with .command / .tool_input.command
cmd="$input"
if command -v jq >/dev/null 2>&1; then
  parsed=$(printf '%s' "$input" | jq -r '.tool_input.command // .command // .input.command // empty' 2>/dev/null || true)
  if [[ -n "${parsed:-}" ]]; then cmd="$parsed"; fi
fi

# Normalize
flat=$(printf '%s' "$cmd" | tr '\n' ' ')

patterns=(
  'rm[[:space:]]+-[a-zA-Z]*r[a-zA-Z]*[[:space:]]+/($|[[:space:]])'
  'rm[[:space:]]+-[a-zA-Z]*r[a-zA-Z]*[[:space:]]+/\*'
  'rm[[:space:]]+-rf[[:space:]]+/'
  'rm[[:space:]]+-fr[[:space:]]+/'
  'mkfs\.'
  'dd[[:space:]]+.*of=/dev/'
  '>\s*/dev/sd[a-z]'
  'chmod[[:space:]]+-R[[:space:]]+777[[:space:]]+/'
  'curl[[:space:]].*\|[[:space:]]*(ba)?sh'
  'wget[[:space:]].*\|[[:space:]]*(ba)?sh'
  'git[[:space:]]+push[[:space:]]+.*--force[[:space:]]+.*(main|master)'
  'git[[:space:]]+push[[:space:]]+-f[[:space:]]+.*(main|master)'
  'DROP[[:space:]]+TABLE'
  'DROP[[:space:]]+DATABASE'
  'truncate[[:space:]]+table'
  ':()\{ :\|:& \};:'
  'mv[[:space:]]+/[[:space:]]'
  'chmod[[:space:]]+000[[:space:]]+/'
)

for re in "${patterns[@]}"; do
  if printf '%s' "$flat" | grep -Eiq -- "$re"; then
    echo "BLOCKED destructive bash pattern: /$re/" >&2
    echo "command: $flat" >&2
    exit 2
  fi
done

exit 0
