#!/usr/bin/env bash
# Claude Code PreToolUse hook: block destructive shell commands.
#
# Reads the hook payload on stdin, inspects tool_input.command and, if it matches
# a destructive pattern, prints a `deny` decision and logs the attempt to
# ~/.claude/hooks/blocked.log. Everything else exits silently (exit 0) so normal
# Bash calls are untouched.
#
# Escape hatch: CLAUDE_ALLOW_DESTRUCTIVE=1 disables the block (logged as allowed).
#
# Contract: https://code.claude.com/docs/en/hooks (PreToolUse, permissionDecision)

set -u

LOG_DIR="${CLAUDE_HOOK_LOG_DIR:-$HOME/.claude/hooks}"
LOG_FILE="$LOG_DIR/blocked.log"
mkdir -p "$LOG_DIR" 2>/dev/null || true

INPUT="$(cat)"

# Extract one string field from the JSON payload using whatever is available.
json_field() {
  local field="$1"
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$INPUT" | jq -r --arg f "$field" '.[$f] // empty' 2>/dev/null
  elif command -v python3 >/dev/null 2>&1; then
    printf '%s' "$INPUT" | python3 -c 'import json,sys
try:
    data = json.load(sys.stdin)
except Exception:
    data = {}
val = data.get(sys.argv[1])
print(val if isinstance(val, str) else "")' "$field" 2>/dev/null
  elif command -v node >/dev/null 2>&1; then
    printf '%s' "$INPUT" | FIELD="$field" node -e '
let raw = "";
process.stdin.on("data", (c) => (raw += c)).on("end", () => {
  try {
    const v = JSON.parse(raw)[process.env.FIELD];
    process.stdout.write(typeof v === "string" ? v : "");
  } catch { /* ignore */ }
});' 2>/dev/null
  else
    # Last resort: tolerate a compact single-line payload.
    printf '%s' "$INPUT" | sed -n "s/.*\"$field\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p" | head -1
  fi
}

json_nested() {
  # tool_input is an object, so pull .tool_input.<field> with the same fallbacks.
  local field="$1"
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$INPUT" | jq -r --arg f "$field" '.tool_input[$f] // empty' 2>/dev/null
  elif command -v python3 >/dev/null 2>&1; then
    printf '%s' "$INPUT" | python3 -c 'import json,sys
try:
    data = json.load(sys.stdin)
except Exception:
    data = {}
val = (data.get("tool_input") or {}).get(sys.argv[1])
print(val if isinstance(val, str) else "")' "$field" 2>/dev/null
  elif command -v node >/dev/null 2>&1; then
    printf '%s' "$INPUT" | FIELD="$field" node -e '
let raw = "";
process.stdin.on("data", (c) => (raw += c)).on("end", () => {
  try {
    const v = (JSON.parse(raw).tool_input || {})[process.env.FIELD];
    process.stdout.write(typeof v === "string" ? v : "");
  } catch { /* ignore */ }
});' 2>/dev/null
  else
    printf '%s' "$INPUT" | sed -n "s/.*\"$field\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p" | head -1
  fi
}

TOOL_NAME="$(json_field tool_name)"
COMMAND="$(json_nested command)"
CWD="$(json_field cwd)"
[ -n "$CWD" ] || CWD="$PWD"

# Only Bash-like calls carry a shell command; anything else is none of our business.
case "$TOOL_NAME" in
  ""|Bash|bash|PowerShell|powershell|shell) ;;
  *) exit 0 ;;
esac
[ -n "$COMMAND" ] || exit 0

if [ "${CLAUDE_ALLOW_DESTRUCTIVE:-0}" = "1" ]; then
  exit 0
fi

log_block() {
  local reason="$1"
  local flat
  flat="$(printf '%s' "$COMMAND" | tr '\n\r\t' '   ' | cut -c1-500)"
  printf '%s | %s | %s | %s\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$reason" "$CWD" "$flat" >> "$LOG_FILE" 2>/dev/null || true
}

deny() {
  local reason="$1" explanation="$2"
  log_block "$reason"
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' \
    "$explanation"
  exit 0
}

# 1) rm with recursive + force, in any flag order (-rf, -fr, -r -f, --recursive --force)
if printf '%s' "$COMMAND" | grep -Eiq '(^|[^[:alnum:]_])(sudo[[:space:]]+)?rm[[:space:]]+([^;&|]*[[:space:]])?(-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*|-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*|(-r|--recursive)[[:space:]]+(-f|--force)|(-f|--force)[[:space:]]+(-r|--recursive))([[:space:]]|$|[;&|])'; then
  deny "rm recursive+force" "Blocked by the block-destructive hook: this is a recursive force delete (rm -rf). Nothing was executed. If the deletion is really intended, ask the user to run it themselves, or re-run the session with CLAUDE_ALLOW_DESTRUCTIVE=1."
fi

# 2) SQL DROP TABLE
if printf '%s' "$COMMAND" | grep -Eiq '(^|[^[:alnum:]_])drop[[:space:]]+table([^[:alnum:]_]|$)'; then
  deny "DROP TABLE" "Blocked by the block-destructive hook: DROP TABLE destroys a table and its data. Nothing was executed. If it is intentional, ask the user to run it themselves (or use a migration), or re-run with CLAUDE_ALLOW_DESTRUCTIVE=1."
fi

# 3) SQL TRUNCATE
if printf '%s' "$COMMAND" | grep -Eiq '(^|[^[:alnum:]_])truncate([^[:alnum:]_]|$)'; then
  deny "TRUNCATE" "Blocked by the block-destructive hook: TRUNCATE empties a table irreversibly. Nothing was executed. If it is intentional, ask the user to run it themselves, or re-run with CLAUDE_ALLOW_DESTRUCTIVE=1."
fi

# 4) DELETE FROM without WHERE (checked per statement so WHERE on another statement does not mask it)
if printf '%s' "$COMMAND" | tr ';' '\n' | grep -Eiq 'delete[[:space:]]+from'; then
  WITHOUT_WHERE="$(printf '%s' "$COMMAND" | tr ';' '\n' | grep -Ei 'delete[[:space:]]+from' | grep -Eiv 'where' | head -1)"
  if [ -n "$WITHOUT_WHERE" ]; then
    deny "DELETE without WHERE" "Blocked by the block-destructive hook: DELETE FROM without a WHERE clause deletes every row. Nothing was executed. Add a WHERE clause, or ask the user to run it themselves, or re-run with CLAUDE_ALLOW_DESTRUCTIVE=1."
  fi
fi

# 5) git push --force / -f (the safer --force-with-lease is allowed on purpose)
if printf '%s' "$COMMAND" | grep -Eiq 'git[[:space:]]+push'; then
  if printf '%s' "$COMMAND" | grep -Eiq 'git[[:space:]]+push[^;&|]*[[:space:]](-f|--force)([[:space:]]|$|[;&|])'; then
    deny "git push --force" "Blocked by the block-destructive hook: force-pushing rewrites remote history. Nothing was executed. Use --force-with-lease if you must, or ask the user to run it, or re-run with CLAUDE_ALLOW_DESTRUCTIVE=1."
  fi
fi

exit 0
