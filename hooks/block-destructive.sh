#!/usr/bin/env bash
# Claude Code PreToolUse hook — blocks destructive Bash commands.
set -euo pipefail

LOG_FILE="${HOME}/.claude/hooks/blocked.log"

matches_rm_rf() {
  local cmd=$1
  if grep -qiE '\brm[[:space:]]+(-[A-Za-z]*[rf][A-Za-z]*[rf][A-Za-z]*|-[A-Za-z]*[rf][A-Za-z]*[[:space:]]+-[A-Za-z]*[rf])\b' <<<"$cmd"; then
    return 0
  fi
  if grep -qiE '\brm\b' <<<"$cmd" \
    && grep -qiE '(^|[[:space:]])--recursive([[:space:]]|$)' <<<"$cmd" \
    && grep -qiE '(^|[[:space:]])--force([[:space:]]|$)' <<<"$cmd"; then
    return 0
  fi
  return 1
}

matches_drop_table() {
  grep -qiE '\bdrop[[:space:]]+table\b' <<<"$1"
}

matches_force_push() {
  local cmd=$1
  if ! grep -qiE '\bgit[[:space:]]+push\b' <<<"$cmd"; then
    return 1
  fi
  if grep -qiE '(^|[[:space:]])--force-with-lease([[:space:]]|$)' <<<"$cmd"; then
    return 1
  fi
  grep -qiE '(^|[[:space:]])--force([[:space:]]|$)|[[:space:]]-f([[:space:]]|$|;|&|\|)' <<<"$cmd"
}

matches_truncate() {
  grep -qiE '\btruncate([[:space:]]+table)?\b' <<<"$1"
}

matches_unscoped_delete() {
  local cmd=$1
  local stmt
  local old_ifs=$IFS
  IFS=$';\n'
  for stmt in $cmd; do
    stmt=$(sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' <<<"$stmt")
    [[ -z "$stmt" ]] && continue
    if grep -qiE '\bdelete[[:space:]]+from\b' <<<"$stmt" && ! grep -qiE '\bwhere\b' <<<"$stmt"; then
      IFS=$old_ifs
      return 0
    fi
  done
  IFS=$old_ifs
  return 1
}

INPUT=$(cat)
if [[ -z "$INPUT" ]]; then
  exit 0
fi

TOOL_NAME=$(jq -r '.tool_name // empty' <<<"$INPUT")
if [[ "$TOOL_NAME" != "Bash" ]]; then
  exit 0
fi

COMMAND=$(jq -r '.tool_input.command // empty' <<<"$INPUT")
if [[ -z "$COMMAND" ]]; then
  exit 0
fi

PROJECT_PATH=$(jq -r '.cwd // empty' <<<"$INPUT")
if [[ -z "$PROJECT_PATH" ]]; then
  PROJECT_PATH=$(pwd)
fi

reason=""

if matches_rm_rf "$COMMAND"; then
  reason="Blocked rm -rf: recursively deletes files and directories with no recovery prompt."
elif matches_drop_table "$COMMAND"; then
  reason="Blocked DROP TABLE: permanently removes a database table and its data."
elif matches_force_push "$COMMAND"; then
  reason="Blocked git push --force: overwrites remote history and can destroy teammates' work."
elif matches_truncate "$COMMAND"; then
  reason="Blocked TRUNCATE: removes all rows from a table without row-level filtering."
elif matches_unscoped_delete "$COMMAND"; then
  reason="Blocked DELETE FROM without WHERE: deletes every row in the target table."
fi

if [[ -z "$reason" ]]; then
  exit 0
fi

mkdir -p "$(dirname "$LOG_FILE")"
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
jq -nc \
  --arg ts "$timestamp" \
  --arg cmd "$COMMAND" \
  --arg path "$PROJECT_PATH" \
  '{timestamp: $ts, command: $cmd, project_path: $path}' >>"$LOG_FILE"

jq -n \
  --arg reason "$reason" \
  '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: $reason
    }
  }'

exit 0
