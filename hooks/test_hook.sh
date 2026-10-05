#!/usr/bin/env bash
# test_hook.sh — tests for block-destructive-commands.sh (real execution).
set -uo pipefail

SCRIPT="$(cd "$(dirname "$0")" && pwd)/block-destructive-commands.sh"
PASS=0; FAIL=0
LOG="$(mktemp)"
export BLOCKED_LOG="$LOG"
TRACK="$(mktemp)"
trap 'rm -f "$LOG" "$TRACK"' EXIT

ok()   { PASS=$((PASS+1)); echo "ok   $1"; }
bad()  { FAIL=$((FAIL+1)); echo "FAIL $1"; }

hook() { # $1 = command string -> hook stdout
    local cmd="$1"
    python3 -c 'import json,sys; print(json.dumps({"tool_name":"Bash","tool_input":{"command":sys.argv[1]},"cwd":"/proj"}))' "$cmd" \
        | BLOCKED_LOG="$LOG" bash "$SCRIPT"
}

expect_block() { # $1 = command, $2 = name
    local out
    out="$(hook "$1")"
    if [[ "$out" == *'"decision": "block"'* || "$out" == *'"decision":"block"'* ]]; then
        ok "$2"
    else
        bad "$2 (got: ${out:0:80})"
    fi
}

expect_allow() { # $1 = command, $2 = name
    local out rc
    out="$(hook "$1")"; rc=$?
    if [[ -z "$out" && $rc -eq 0 ]]; then
        ok "$2"
    else
        bad "$2 (rc=$rc out: ${out:0:80})"
    fi
}

# --- rm -rf variants ---
expect_block "rm -rf /" "rm -rf / blocked"
expect_block "rm -rf ~" "rm -rf ~ blocked"
expect_block "rm -fr /tmp/x" "rm -fr blocked"
expect_block "rm --recursive --force /data" "long opts blocked"
expect_block "rm -r -f /tmp/x" "split flags blocked"
expect_block "rm -r --force /tmp/x" "mixed short+long blocked"
expect_block "echo hi; rm -rf /tmp/x" "chained rm blocked"
expect_block "sudo rm -rf /" "sudo rm blocked"
expect_block "RM -RF /" "uppercase blocked"
expect_allow "rm -f file.txt" "rm -f allowed"
expect_allow "rm -r somedir" "rm -r allowed"
expect_allow "rm -f --dry-run" "dry-run allowed"
expect_allow "ls -la /tmp" "ls allowed"

# --- SQL ---
expect_block "DROP TABLE users" "drop table blocked"
expect_block "drop table users" "lowercase drop blocked"
expect_block "TRUNCATE TABLE logs" "truncate blocked"
expect_block "truncate logs" "truncate w/o table blocked"
expect_block "DELETE FROM users" "delete w/o where blocked"
expect_allow "DELETE FROM users WHERE id=1" "delete with where allowed"
expect_allow "SELECT * FROM users" "select allowed"

# --- git ---
expect_block "git push --force" "push --force blocked"
expect_block "git push origin main --force" "push --force mid blocked"
expect_block "git push -f origin main" "push -f blocked"
expect_allow "git push --force-with-lease" "force-with-lease allowed"
expect_allow "git push origin main" "normal push allowed"

# --- protocol ---
out="$(python3 -c 'import json; print(json.dumps({"tool_name":"Read","tool_input":{"file_path":"/x"},"cwd":"/proj"}))' | bash "$SCRIPT")"
[[ -z "$out" ]] && ok "non-bash ignored" || bad "non-bash ignored"
printf 'not json{{{' | bash "$SCRIPT" >/dev/null 2>&1
[[ $? -eq 0 ]] && ok "malformed fails open" || bad "malformed fails open"

# --- logging ---
: > "$LOG"
hook "rm -rf /" >/dev/null
if grep -q "rm -rf /" "$LOG" && grep -q "/proj" "$LOG" && grep -qE '[0-9]{4}-[0-9]{2}-[0-9]{2}T' "$LOG"; then
    ok "blocked logged (ts+cmd+cwd)"
else
    bad "blocked logged"
fi
: > "$LOG"
hook "ls -la" >/dev/null
[[ ! -s "$LOG" ]] && ok "allowed not logged" || bad "allowed not logged"

# --- reason message ---
out="$(hook "rm -rf /")"
[[ "$out" == *'"reason"'* ]] && ok "reason present" || bad "reason present"

# --- current protocol format (hookSpecificOutput) ---
out="$(hook "rm -rf /")"
if [[ "$out" == *'"hookSpecificOutput"'* && "$out" == *'"hookEventName":"PreToolUse"'* \
      && "$out" == *'"permissionDecision":"deny"'* ]]; then
    ok "deny via hookSpecificOutput"
else
    bad "deny via hookSpecificOutput (got: ${out:0:120})"
fi

# --- regression: bypasses found in review ---
expect_block "git push --force-with-lease --force" "lease+force blocked"
expect_block 'psql -c "DELETE FROM old WHERE x=1; DELETE FROM users"' "per-statement delete blocked"
expect_allow 'psql -c "DELETE FROM users WHERE id=1"' "single where delete allowed"
expect_block 'mysql -e "DELETE FROM `users`"' "backtick table blocked"

echo
echo "passed: $PASS, failed: $FAIL"
[[ $FAIL -eq 0 ]]
