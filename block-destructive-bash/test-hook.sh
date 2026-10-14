#!/usr/bin/env bash
# Test harness for block-destructive-bash.sh
# Feeds JSON payloads through the hook, asserts exit codes and log contents.
set -uo pipefail
HOOK="$(dirname "$0")/block-destructive-bash.sh"
export BLOCKED_LOG="$(mktemp)"
export CLAUDE_PROJECT_DIR="/tmp/test-project"
PASS=0; FAIL=0

check() {
    # $1 = description, $2 = expected (block|allow), $3 = command
    local desc="$1" expect="$2" cmd="$3"
    local payload
    payload="$(printf '{"tool_name":"Bash","tool_input":{"command":%s}}' \
        "$(printf '%s' "$cmd" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')")"
    local err rc
    err="$(printf '%s' "$payload" | bash "$HOOK" 2>&1)"; rc=$?
    local got
    if [[ $rc -eq 2 ]]; then got="block"; else got="allow"; fi
    if [[ "$got" == "$expect" ]]; then
        PASS=$((PASS+1)); printf 'PASS  %-58s -> %s\n' "$desc" "$got"
    else
        FAIL=$((FAIL+1)); printf 'FAIL  %-58s -> %s (expected %s, rc=%s)\n' "$desc" "$got" "$expect" "$rc"
    fi
}

echo "=== MUST BLOCK (exit 2):"
check "rm -rf /"                          block "rm -rf /"
check "sudo rm -rf ./build"               block "sudo rm -rf ./build"
check "rm -fr node_modules"               block "rm -fr node_modules"
check "rm -r -f dist"                     block "rm -r -f dist"
check "rm --recursive --force cache"      block "rm --recursive --force cache"
check "git push --force origin main"      block "git push --force origin main"
check "git push -f"                       block "git push -f"
check "DROP TABLE users;"                 block "psql -c 'DROP TABLE users;'"
check "TRUNCATE TABLE sessions"           block "TRUNCATE TABLE sessions"
check "DELETE FROM users (no WHERE)"      block "DELETE FROM users"
check "git reset --hard HEAD~5"           block "git reset --hard HEAD~5"

echo
echo "=== MUST ALLOW (exit 0):"
check "rm single file"                    allow "rm notes.txt"
check "rm -r without -f"                  allow "rm -r empty-dir"
check "git push"                          allow "git push origin main"
check "git push --force-with-lease"       allow "git push --force-with-lease origin main"
check "DELETE FROM with WHERE"            allow "DELETE FROM users WHERE id = 42"
check "SELECT query"                      allow "psql -c 'SELECT * FROM users;'"
check "ls -la"                            allow "ls -la"
check "echo hello"                        allow "echo hello"
check "git commit"                        allow "git commit -m 'wip'"

echo
echo "=== NON-BASH TOOL PASSES:"
payload='{"tool_name":"Edit","tool_input":{"file_path":"/tmp/x","new_string":"rm -rf /"}}'
err="$(printf '%s' "$payload" | bash "$HOOK" 2>&1)"; rc=$?
if [[ $rc -eq 0 ]]; then PASS=$((PASS+1)); echo "PASS  Edit tool with rm -rf in content    -> allow"; else FAIL=$((FAIL+1)); echo "FAIL  Edit tool should pass (rc=$rc)"; fi

echo
echo "=== LOG CONTENTS:"
if [[ -s "$BLOCKED_LOG" ]]; then
    lines=$(wc -l < "$BLOCKED_LOG")
    echo "blocked.log has $lines entries; sample:"
    head -2 "$BLOCKED_LOG"
    # validate JSON structure of every line
    if python3 -c "
import json, sys
ok = True
for line in open('$BLOCKED_LOG'):
    d = json.loads(line)
    for k in ('ts', 'command', 'project', 'reason'):
        if k not in d: ok = False; print('missing field:', k)
print('all log lines are valid JSON with ts/command/project/reason' if ok else 'LOG SCHEMA BROKEN')
sys.exit(0 if ok else 1)
"; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi
else
    FAIL=$((FAIL+1)); echo "FAIL  blocked.log is empty but 11 blocks were expected"
fi

echo
echo "RESULT: $PASS passed, $FAIL failed"
rm -f "$BLOCKED_LOG"
exit $((FAIL > 0))
