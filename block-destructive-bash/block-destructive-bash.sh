#!/usr/bin/env bash
# pre-tool-use hook: block destructive bash commands before execution.
#
# Claude Code invokes PreToolUse hooks with a JSON payload on stdin:
#   {"tool_name": "Bash", "tool_input": {"command": "..."}}
# Exit 0  -> allow the command through, silently
# Exit 2  -> block the command; stderr is shown to Claude as the reason
#
# Every blocked attempt is appended to ~/.claude/hooks/blocked.log as a JSON
# line: {"ts": ..., "command": ..., "project": ..., "reason": ...}

set -uo pipefail

LOG_FILE="${BLOCKED_LOG:-$HOME/.claude/hooks/blocked.log}"
# parameter expansion instead of dirname: keeps the hook dependency-free
case "$LOG_FILE" in */*) mkdir -p "${LOG_FILE%/*}" ;; esac

payload="$(cat)"

# --- extract tool name and command from the stdin payload ---
# jq when available; a python3 fallback otherwise (no hard dependency).
if command -v jq >/dev/null 2>&1; then
    tool_name="$(printf '%s' "$payload" | jq -r '.tool_name // empty')"
    command_str="$(printf '%s' "$payload" | jq -r '.tool_input.command // empty')"
else
    eval "$(printf '%s' "$payload" | python3 -c '
import json, sys, shlex
try:
    d = json.load(sys.stdin)
except Exception:
    d = {}
print("tool_name=" + shlex.quote(str(d.get("tool_name") or "")))
print("command_str=" + shlex.quote(str((d.get("tool_input") or {}).get("command") or "")))
')"
fi

# Only police Bash tool calls; everything else passes untouched.
[[ "$tool_name" == "Bash" ]] || exit 0
[[ -n "$command_str" ]] || exit 0

log_and_block() {
    # $1 = reason shown to Claude
    local reason="$1"
    local ts project
    ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    project="${CLAUDE_PROJECT_DIR:-$PWD}"
    printf '{"ts":"%s","command":%s,"project":"%s","reason":"%s"}\n' \
        "$ts" "$(printf '%s' "$command_str" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))' 2>/dev/null || printf '"%s"' "${command_str//\"/\\\"}")" \
        "$project" "$reason" >> "$LOG_FILE"
    echo "BLOCKED: $reason" >&2
    echo "Command: $command_str" >&2
    echo "If this was intentional, the user can run it themselves outside Claude Code." >&2
    exit 2
}

# --- pattern checks (each a real destructive class from the bounty spec) ---

# 1. rm -rf / rm -fr / rm -r -f / sudo variants — both -r and -f present,
#    whether combined (-rf), reversed (-fr), or as separate tokens (-r -f).
if [[ "$command_str" =~ (^|[[:space:];&|])(sudo[[:space:]]+)?rm([[:space:]]|$) ]]; then
    # NOTE: || and && do not mix without explicit grouping: A || B && C parses
    # as (A || B) && C. Scan conservatively across the whole command (a safety
    # hook errs toward blocking; the block message says how to proceed).
    has_r=0; has_f=0
    [[ "$command_str" =~ (^|[[:space:]])-[a-zA-Z]*r[a-zA-Z]*([[:space:]]|$) || "$command_str" =~ --recursive ]] && has_r=1
    [[ "$command_str" =~ (^|[[:space:]])-[a-zA-Z]*f[a-zA-Z]*([[:space:]]|$) || "$command_str" =~ --force ]] && has_f=1
    if [[ $has_r -eq 1 && $has_f -eq 1 ]]; then
        log_and_block "recursive force delete (rm -rf) destroys files irreversibly"
    fi
fi

# 2. git push --force / -f (--force-with-lease is the safe alternative and passes).
if [[ "$command_str" =~ git[[:space:]]+push ]]; then
    if [[ "$command_str" =~ (^|[[:space:]])(--force([[:space:]]|$)|-f([[:space:]]|$)) ]]; then
        log_and_block "git push --force rewrites remote history; use --force-with-lease instead"
    fi
fi

# 3. DROP TABLE / TRUNCATE — SQL that destroys data wholesale.
if [[ "$command_str" =~ (DROP[[:space:]]+TABLE|TRUNCATE([[:space:]]+TABLE)?[[:space:]]) ]]; then
    log_and_block "SQL DROP TABLE / TRUNCATE destroys data wholesale"
fi

# 4. DELETE FROM without a WHERE clause.
if [[ "$command_str" =~ DELETE[[:space:]]+FROM ]]; then
    if ! [[ "$command_str" =~ WHERE ]]; then
        log_and_block "DELETE FROM without a WHERE clause deletes every row"
    fi
fi

# 5. git reset --hard discards uncommitted work.
if [[ "$command_str" =~ git[[:space:]]+reset[[:space:]]+--hard ]]; then
    log_and_block "git reset --hard discards uncommitted changes irreversibly"
fi

exit 0
