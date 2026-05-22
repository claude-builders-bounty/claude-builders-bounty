#!/usr/bin/env bash
# Claude Code PreToolUse hook — blocks destructive bash commands before execution.
#
# Input  : JSON via stdin with { tool_name, tool_input.command, cwd }
# Output :
#   - safe command  -> exit 0 (silent pass-through)
#   - dangerous     -> JSON to stdout with permissionDecision=deny, exit 0
#   - non-Bash tool -> exit 0 (pass-through, no inspection)
#
# Dependencies: bash 4+, grep — that's it. No jq, no Python.
# Logs        : ~/.claude/hooks/blocked.log

set -uo pipefail

LOG_DIR="${HOME}/.claude/hooks"
LOG_FILE="${LOG_DIR}/blocked.log"
mkdir -p "${LOG_DIR}"

# Read full JSON payload from stdin
PAYLOAD="$(cat)"

# --- Tiny pure-bash JSON value extractor ---
# Extracts the string value of a top-level or nested key.
# Handles escaped quotes and common control characters.
# Returns empty string if not found.
extract_json_string() {
    local json="$1"
    local key="$2"
    # Look for "key" : "value" pattern; handle escapes inside value
    # Use a Perl-like approach via grep -oP
    if command -v grep >/dev/null 2>&1 && echo "" | grep -oP "" >/dev/null 2>&1; then
        # grep -P (PCRE) is available
        echo "${json}" | grep -oP "\"${key}\"\\s*:\\s*\"(\\\\.|[^\"\\\\])*\"" | head -1 \
            | sed -E "s/^\"${key}\"\\s*:\\s*\"//; s/\"$//; s/\\\\\"/\"/g; s/\\\\n/\n/g; s/\\\\\\\\/\\\\/g"
    else
        # Fallback: BSD grep without -P. Less robust but works for simple values.
        echo "${json}" | awk -v key="\"${key}\"" '
            BEGIN { RS=""; FS="" }
            {
                idx = index($0, key)
                if (idx > 0) {
                    rest = substr($0, idx + length(key))
                    sub(/^[[:space:]]*:[[:space:]]*"/, "", rest)
                    val = ""
                    escaped = 0
                    for (i = 1; i <= length(rest); i++) {
                        c = substr(rest, i, 1)
                        if (escaped) { val = val c; escaped = 0; continue }
                        if (c == "\\") { val = val c; escaped = 1; continue }
                        if (c == "\"") break
                        val = val c
                    }
                    gsub(/\\"/, "\"", val)
                    gsub(/\\\\/, "\\", val)
                    print val
                    exit
                }
            }'
    fi
}

TOOL_NAME="$(extract_json_string "${PAYLOAD}" "tool_name")"
COMMAND="$(extract_json_string "${PAYLOAD}" "command")"
CWD="$(extract_json_string "${PAYLOAD}" "cwd")"

# Only inspect Bash tool calls
if [[ "${TOOL_NAME}" != "Bash" ]]; then
    exit 0
fi

# No command to inspect
if [[ -z "${COMMAND}" ]]; then
    exit 0
fi

# Lowercase a copy for case-insensitive matching while preserving original for log
COMMAND_LC="$(printf '%s' "${COMMAND}" | tr '[:upper:]' '[:lower:]')"

# Match patterns. Each entry: "<reason>|<regex>"
declare -a PATTERNS=(
    "Recursive force delete (rm -rf)|(^|[[:space:];|&])rm[[:space:]]+(-[a-z]*r[a-z]*f[a-z]*|-[a-z]*f[a-z]*r[a-z]*|--recursive[[:space:]]+--force|--force[[:space:]]+--recursive)"
    "SQL DROP TABLE|drop[[:space:]]+table[[:space:]]"
    "SQL DROP DATABASE|drop[[:space:]]+database[[:space:]]"
    "SQL TRUNCATE|truncate([[:space:]]+table)?[[:space:]]"
    "Force push (git push --force)|git[[:space:]]+push[[:space:]]+([^|;&]*[[:space:]])?(--force([[:space:]]|$)|-f([[:space:]]|$))"
    "Filesystem format (mkfs)|(^|[[:space:];|&])mkfs(\\.|[[:space:]])"
    "Direct disk write (dd to /dev/)|dd[[:space:]]+[^|;&]*of=/dev/(sd|hd|nvme|disk)"
    "Block device overwrite (> /dev/sd)|>[[:space:]]*/dev/(sd|hd|nvme|disk)"
    "Recursive permission change on root|chmod[[:space:]]+(-[a-z]*r[a-z]*[[:space:]]+|--recursive[[:space:]]+)777[[:space:]]+/"
    "Recursive ownership change on root|chown[[:space:]]+(-[a-z]*r[a-z]*|--recursive)[[:space:]]+[^[:space:]]+[[:space:]]+/"
)

# DELETE FROM <table> without WHERE — handled separately
check_delete_without_where() {
    if echo "${COMMAND_LC}" | grep -iE 'delete[[:space:]]+from[[:space:]]+[^;|&]+' >/dev/null; then
        delete_clause="$(echo "${COMMAND_LC}" | grep -oiE 'delete[[:space:]]+from[[:space:]]+[^;|&]+' | head -1)"
        if ! echo "${delete_clause}" | grep -iE '[[:space:]]where[[:space:]]' >/dev/null; then
            return 0
        fi
    fi
    return 1
}

MATCHED_REASON=""

for entry in "${PATTERNS[@]}"; do
    reason="${entry%%|*}"
    regex="${entry#*|}"
    if echo "${COMMAND_LC}" | grep -iE "${regex}" >/dev/null 2>&1; then
        MATCHED_REASON="${reason}"
        break
    fi
done

if [[ -z "${MATCHED_REASON}" ]] && check_delete_without_where; then
    MATCHED_REASON="SQL DELETE without WHERE clause"
fi

# Safe — pass through
if [[ -z "${MATCHED_REASON}" ]]; then
    exit 0
fi

# Dangerous — log and deny
TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
printf '[%s] BLOCKED | pattern="%s" | project="%s" | command="%s"\n' \
    "${TIMESTAMP}" "${MATCHED_REASON}" "${CWD}" "${COMMAND}" >> "${LOG_FILE}"

# JSON-escape a string for safe embedding
json_escape() {
    local s="$1"
    s="${s//\\/\\\\}"
    s="${s//\"/\\\"}"
    s="${s//$'\n'/\\n}"
    s="${s//$'\r'/\\r}"
    s="${s//$'\t'/\\t}"
    printf '%s' "${s}"
}

REASON_ESC="$(json_escape "${MATCHED_REASON}")"
COMMAND_ESC="$(json_escape "${COMMAND}")"
LOG_ESC="$(json_escape "${LOG_FILE}")"

cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Command blocked by pre-tool-use safety hook.\\n\\nReason: ${REASON_ESC}\\n\\nCommand: ${COMMAND_ESC}\\n\\nThis pattern is on the destructive-commands blocklist because it can cause irreversible data loss.\\nIf you are certain this is necessary:\\n  1. Explain the impact to the user\\n  2. Ask for explicit confirmation\\n  3. Have the user run the command themselves in their terminal\\n\\nLogged to: ${LOG_ESC}"
  }
}
EOF

exit 0
