#!/usr/bin/env bash
#
# block_destructive.sh - Claude Code pre-tool-use hook
#
# Blocks destructive bash commands before they execute.
# Receives JSON on stdin: { "tool_name": "...", "tool_input": { "command": "..." } }
# Outputs JSON:  { "decision": "allow" }  or  { "decision": "block", "reason": "..." }
#

set -euo pipefail

LOG_FILE="$HOME/.claude/hooks/blocked.log"

# Read the full JSON payload from stdin
input="$(cat)"

# Extract tool_name
tool_name="$(echo "$input" | jq -r '.tool_name // empty')"

# Only inspect Bash tool invocations; allow everything else immediately
if [[ "$tool_name" != "Bash" ]]; then
  echo '{"decision":"allow"}'
  exit 0
fi

# Extract the command string
command_raw="$(echo "$input" | jq -r '.tool_input.command // empty')"

# If there is no command, nothing to block
if [[ -z "$command_raw" ]]; then
  echo '{"decision":"allow"}'
  exit 0
fi

# Normalize: collapse whitespace and convert to lowercase for pattern matching
command_normalized="$(echo "$command_raw" | tr '[:upper:]' '[:lower:]' | tr -s '[:space:]' ' ')"

# ── helper: log a blocked attempt ──────────────────────────────────────────────
log_block() {
  local reason="$1"
  mkdir -p "$(dirname "$LOG_FILE")"
  local timestamp
  timestamp="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  local project_path="${PWD:-unknown}"
  # Append a JSON-lines entry
  printf '{"timestamp":"%s","project":"%s","reason":"%s","command":%s}\n' \
    "$timestamp" \
    "$project_path" \
    "$reason" \
    "$(echo "$command_raw" | jq -Rs '.')" \
    >> "$LOG_FILE"
}

# ── helper: emit a block verdict and exit ──────────────────────────────────────
block() {
  local reason="$1"
  log_block "$reason"
  jq -n --arg reason "$reason" '{"decision":"block","reason":$reason}'
  exit 0
}

# ── Pattern checks ─────────────────────────────────────────────────────────────

# 1. rm -rf  (matches rm -rf, rm -r -f, rm -fr, rm --recursive --force, etc.)
#    We look for `rm` followed by flags that include both -r and -f in any order.
if echo "$command_normalized" | grep -qE '(^|[;&|] *)rm\b'; then
  # Extract everything after 'rm' up to the next command separator or end
  rm_segment="$(echo "$command_normalized" | grep -oE '(^|[;&|] *)rm [^;&|]*' | head -1)"
  # Check for recursive + force combination
  has_recursive=false
  has_force=false

  if echo "$rm_segment" | grep -qE -- '--recursive'; then
    has_recursive=true
  fi
  if echo "$rm_segment" | grep -qE -- '--force'; then
    has_force=true
  fi
  # Check short flags: could be -rf, -fr, -r -f, etc.
  if echo "$rm_segment" | grep -qE -- '-[a-z]*r[a-z]*'; then
    has_recursive=true
  fi
  if echo "$rm_segment" | grep -qE -- '-[a-z]*f[a-z]*'; then
    has_force=true
  fi

  if $has_recursive && $has_force; then
    block "Destructive command blocked: rm with recursive and force flags (rm -rf)"
  fi
fi

# 2. DROP TABLE
if echo "$command_normalized" | grep -qE 'drop[[:space:]]+table'; then
  block "Destructive SQL blocked: DROP TABLE"
fi

# 3. git push --force (also catches -f shorthand for push)
if echo "$command_normalized" | grep -qE 'git[[:space:]]+push[[:space:]].*--force'; then
  block "Destructive git command blocked: git push --force"
fi
if echo "$command_normalized" | grep -qE 'git[[:space:]]+push[[:space:]].*-f'; then
  # Make sure -f is a standalone flag for push, not part of another word
  if echo "$command_normalized" | grep -qE 'git[[:space:]]+push[[:space:]]+(.*[[:space:]])?-f([[:space:]]|$)'; then
    block "Destructive git command blocked: git push --force (-f)"
  fi
fi

# 4. TRUNCATE (SQL)
if echo "$command_normalized" | grep -qE '(^|[^a-z])truncate[[:space:]]+'; then
  block "Destructive SQL blocked: TRUNCATE"
fi

# 5. DELETE FROM without WHERE
#    We match "delete from <something>" and verify there is no "where" clause following it
if echo "$command_normalized" | grep -qE 'delete[[:space:]]+from[[:space:]]'; then
  # Check if there is a WHERE clause anywhere after DELETE FROM
  if ! echo "$command_normalized" | grep -qE 'delete[[:space:]]+from[[:space:]]+.*where[[:space:]]'; then
    block "Destructive SQL blocked: DELETE FROM without a WHERE clause"
  fi
fi

# ── All checks passed ─────────────────────────────────────────────────────────
echo '{"decision":"allow"}'
exit 0
