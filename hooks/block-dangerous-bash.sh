#!/usr/bin/env bash
set -euo pipefail

payload="$(cat)"

extract_json_string() {
  local key="$1"
  local json="$2"

  printf '%s' "$json" |
    sed -n "s/.*\"$key\"[[:space:]]*:[[:space:]]*\"\\([^\"\\\\]*\\(\\\\.[^\"\\\\]*\\)*\\)\".*/\\1/p" |
    sed 's/\\"/"/g; s/\\\\/\\/g'
}

json_escape() {
  local value="$1"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  value="${value//$'\n'/\\n}"
  printf '%s' "$value"
}

tool_name="$(extract_json_string "tool_name" "$payload")"
command="$(extract_json_string "command" "$payload")"
project_path="$(extract_json_string "cwd" "$payload")"

if [[ "$tool_name" != "Bash" || -z "$command" ]]; then
  exit 0
fi

command_lc="$(printf '%s' "$command" | tr '[:upper:]' '[:lower:]')"
reason=""

case "$command_lc" in
  *rm[[:space:]]-rf*|*rm[[:space:]]-[!-]*rf*|*rm[[:space:]]-[!-]*fr*)
    reason="Blocked dangerous rm -rf command."
    ;;
  *git[[:space:]]push*--force*)
    reason="Blocked dangerous git push --force command."
    ;;
  *drop[[:space:]]table*)
    reason="Blocked destructive SQL command: DROP TABLE."
    ;;
  *truncate*)
    reason="Blocked destructive SQL command: TRUNCATE."
    ;;
  *delete[[:space:]]from*)
    if [[ "$command_lc" != *where* ]]; then
      reason="Blocked destructive SQL command: DELETE FROM without WHERE."
    fi
    ;;
esac

if [[ -z "$reason" ]]; then
  exit 0
fi

log_dir="${HOME:-$PWD}/.claude/hooks"
mkdir -p "$log_dir"
log_file="$log_dir/blocked.log"
timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
printf '[%s] project=%s command=%s reason=%s\n' \
  "$timestamp" \
  "${project_path:-unknown}" \
  "$command" \
  "$reason" >> "$log_file"

escaped_reason="$(json_escape "$reason")"
printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$escaped_reason"
