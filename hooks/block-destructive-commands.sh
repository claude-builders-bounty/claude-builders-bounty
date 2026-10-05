#!/usr/bin/env bash
# block-destructive-commands.sh — Claude Code PreToolUse hook.
#
# Reads hook JSON from stdin, blocks destructive bash commands before they run:
#   rm -rf variants | DROP TABLE | TRUNCATE | git push --force(-f) |
#   DELETE FROM without WHERE
# Blocked attempts are logged to ~/.claude/hooks/blocked.log
# (override with BLOCKED_LOG env var, useful for tests).
#
# Protocol: input JSON on stdin {tool_name, tool_input.command, cwd};
#   block: stdout {"decision":"block","reason":"..."} + exit 0
#   allow: exit 0, no output  (malformed input fails open -> allow)
set -uo pipefail

LOG_FILE="${BLOCKED_LOG:-$HOME/.claude/hooks/blocked.log}"

# --- 1. read + parse hook JSON -------------------------------------------
INPUT="$(cat)" || exit 0

parse_input() {
    # prints: tool_name \t command \t cwd   (control chars in values -> space)
    if command -v python3 >/dev/null 2>&1; then
        printf '%s' "$INPUT" | python3 -c '
import json, sys
try:
    d = json.loads(sys.stdin.read())
except Exception:
    sys.exit(1)
def clean(v):
    return v.replace("\t", " ").replace("\n", " ") if isinstance(v, str) else ""
inp = d.get("tool_input", {}) or {}
sys.stdout.write(clean(d.get("tool_name", "")) + "\t"
                 + clean(inp.get("command", "") if isinstance(inp, dict) else "") + "\t"
                 + clean(d.get("cwd", "")))
' 2>/dev/null || return 1
    else
        # best-effort fallback (flat "key": "value" only)
        local cmd cwd
        cmd="$(printf '%s' "$INPUT" | sed -n 's/.*"command"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)"
        cwd="$(printf '%s' "$INPUT" | sed -n 's/.*"cwd"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)"
        printf '%s\t%s\t%s' "Bash" "$cmd" "$cwd"
    fi
}

PARSED="$(parse_input)" || exit 0
TOOL_NAME="${PARSED%%$'\t'*}"
REST="${PARSED#*$'\t'}"
COMMAND="${REST%%$'\t'*}"
CWD="${REST#*$'\t'}"
[[ -z "$CWD" ]] && CWD="$PWD"

# only inspect Bash tool calls that carry a command
if [[ "$TOOL_NAME" != "Bash" || -z "$COMMAND" ]]; then
    exit 0
fi

# --- 2. helpers ------------------------------------------------------------
json_escape() {
    if command -v python3 >/dev/null 2>&1; then
        python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))' <<< "$1" 2>/dev/null
    else
        printf '"%s"' "$(printf '%s' "$1" | tr -d '"')"
    fi
}

do_block() {
    # $1 = matched pattern label
    local ts logdir reason esc
    ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    logdir="$(dirname "$LOG_FILE")"
    mkdir -p "$logdir" 2>/dev/null || true
    printf '%s | %s | %s\n' "$ts" "$CWD" "$COMMAND" >> "$LOG_FILE" 2>/dev/null || true
    reason="Blocked destructive command ($1): $COMMAND. This pattern can cause irreversible data loss or forced overwrites. If you genuinely intend this, explain why it is safe and ask the user to run it themselves."
    esc="$(json_escape "$reason")"
    # Current protocol: PreToolUse decision lives inside hookSpecificOutput
    # (permissionDecision deny; hookEventName required). Top-level decision
    # kept as well for older Claude Code versions that still read it.
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":%s},"decision":"block","reason":%s}\n' "$esc" "$esc"
    exit 0
}

# strip one layer of surrounding quotes from a token (catches "rm" obfuscation)
unquote() {
    local t="$1" dq='"' sq="'"
    t="${t#$dq}"; t="${t%$dq}"
    t="${t#$sq}"; t="${t%$sq}"
    printf '%s' "$t"
}

# --- 3. detection ----------------------------------------------------------
lower="$(printf '%s' "$COMMAND" | tr '[:upper:]' '[:lower:]')"

# 3a. rm -rf variants, checked per ;-separated command segment.
# Token-based: rm command + a recursive flag + a force flag.
# Long opts only count when exact (--recursive/--force); this keeps
# "rm -f --dry-run" allowed while "rm -r --force" is blocked.
check_rm() {
    # $1 = one lowercased command segment
    local s="$1" tok has_r=0 has_f=0 is_rm=0
    for tok in $s; do                       # intentional word splitting
        tok="$(unquote "$tok")"
        case "$tok" in
            rm|*/rm) is_rm=1 ;;
        esac
        case "$tok" in
            --recursive) has_r=1 ;;
            --force)     has_f=1 ;;
            --*)         ;;                  # other long opts don't count
            -*r*)        has_r=1 ;;
        esac
        case "$tok" in
            --force)     has_f=1 ;;
            --*)         ;;
            -*f*)        has_f=1 ;;
        esac
    done
    [[ $is_rm -eq 1 && $has_r -eq 1 && $has_f -eq 1 ]]
}

segs="$(printf '%s' "$lower" | sed -e 's/&&/;/g' -e 's/||/;/g' -e 's/|/;/g')"
while IFS= read -r seg; do
    if check_rm "$seg"; then
        do_block "rm -rf"
    fi
done <<< "$segs"

# 3b. SQL destructive patterns (DROP/TRUNCATE: whole command)
drop_re='(^|[[:space:];\(])drop[[:space:]]+table([[:space:];]|$)'
if [[ "$lower" =~ $drop_re ]]; then
    do_block "DROP TABLE"
fi
truncate_re='(^|[[:space:];\(])truncate([[:space:]]+table)?[[:space:]]'
if [[ "$lower" =~ $truncate_re ]]; then
    do_block "TRUNCATE"
fi
# Each DELETE..table is checked against the text that follows it up to the
# next ";" (its own statement): only a WHERE inside the same statement saves it.
# Table name accepts MySQL backticks and SQL Server brackets too.
check_delete() {
    # $1 = lowercased command
    local tmp="$1" m rest scope
    local del_re='delete[[:space:]]+from[[:space:]]+[][a-z0-9_".`]+'
    local where_re='[[:space:]]where[[:space:]]'
    while [[ "$tmp" =~ $del_re ]]; do
        m="${BASH_REMATCH[0]}"
        rest="${tmp#*"$m"}"
        scope="${rest%%;*}"
        if [[ ! "$scope" =~ $where_re ]]; then
            do_block "DELETE FROM without WHERE"
        fi
        tmp="${rest#*;}"
        [[ "$tmp" == "$rest" ]] && break
    done
}
check_delete "$lower"

# 3c. git push --force / -f
# (--force-with-lease ALONE is the safe variant and stays allowed, but a bare
# --force / -f anywhere in the same command wins in git -> still block)
git_re='(^|[[:space:];])git[[:space:]]+push([[:space:]]|$)'
force_re='--force([[:space:]]|$)'
dashf_re='[[:space:]]-f([[:space:]]|$)'
if [[ "$lower" =~ $git_re ]]; then
    if [[ "$lower" =~ $force_re ]] || [[ "$lower" =~ $dashf_re ]]; then
        do_block "git push --force"
    fi
fi

exit 0
