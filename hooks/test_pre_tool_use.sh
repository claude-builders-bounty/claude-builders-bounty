#!/usr/bin/env bash
# Tests for pre-tool-use.sh. Run: bash test_pre_tool_use.sh
set -uo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
HOOK="$HERE/pre-tool-use.sh"
TMP_HOME=$(mktemp -d)
export HOME="$TMP_HOME"
trap 'rm -rf "$TMP_HOME"' EXIT
mkdir -p "$HOME/.claude/hooks"

pass=0
fail=0

run_case() {
  local expected="$1" name="$2" command="$3"
  local out
  out=$(printf '{"tool_input":{"command":%s}}' "$(printf '%s' "$command" | python -c 'import json,sys; print(json.dumps(sys.stdin.read()))')" | bash "$HOOK")
  local got="allow"
  if printf '%s' "$out" | grep -q '"permissionDecision":"deny"'; then
    got="deny"
  fi
  if [[ "$got" == "$expected" ]]; then
    pass=$((pass + 1))
    printf '  ok   %-52s [%s]\n' "$name" "$got"
  else
    fail=$((fail + 1))
    printf '  FAIL %-52s expected=%s got=%s out=%s\n' "$name" "$expected" "$got" "$out"
  fi
}

echo "blocked patterns:"
run_case deny "rm -rf /"                  'rm -rf /'
run_case deny "rm -fr ./build"            'rm -fr ./build'
run_case deny "rm -Rf ./build"            'rm -Rf ./build'
run_case deny "rm -r -f ./build"          'rm -r -f ./build'
run_case deny "rm -f -r ./build"          'rm -f -r ./build'
run_case deny "rm --recursive --force x"  'rm --recursive --force x'
run_case deny "sudo rm -rf /var"          'sudo rm -rf /var'
run_case deny "DROP TABLE users"          'DROP TABLE users;'
run_case deny "drop table if exists t"    'drop table if exists t;'
run_case deny "TRUNCATE TABLE events"     'TRUNCATE TABLE events;'
run_case deny "TRUNCATE events"           'TRUNCATE events;'
run_case deny "DELETE FROM users"         'DELETE FROM users;'
run_case deny "git push --force"          'git push --force origin main'
run_case deny "git push -f"               'git push -f origin main'
run_case deny "mkfs.ext4 /dev/sdb1"       'mkfs.ext4 /dev/sdb1'
run_case deny "dd of=/dev/sda"            'dd if=/dev/zero of=/dev/sda bs=1M'

echo "allowed commands:"
run_case allow "ls -la"                   'ls -la'
run_case allow "rm -r ./build"            'rm -r ./build'
run_case allow "rm file.txt"              'rm file.txt'
run_case allow "git push origin main"     'git push origin main'
run_case allow "git push --force-with-lease" 'git push --force-with-lease origin main'
run_case allow "DELETE FROM users WHERE id=1" 'DELETE FROM users WHERE id=1;'
run_case allow "SELECT * FROM users"      'SELECT * FROM users;'
run_case allow "grep force README"        'grep force README.md'
run_case allow "dd if=disk.img of=out.img" 'dd if=disk.img of=out.img bs=4M'
run_case allow "make build"               'make build'
run_case allow "npm test"                 'npm test'

echo "empty / malformed payload:"
for payload in '' 'not json' '{}' '{"tool_input":{}}'; do
  out=$(printf '%s' "$payload" | bash "$HOOK")
  if [[ -z "$out" ]]; then
    pass=$((pass + 1)); printf '  ok   %-52s [allow]\n' "payload: ${payload:-<empty>}"
  else
    fail=$((fail + 1)); printf '  FAIL %-52s out=%s\n' "payload: ${payload:-<empty>}" "$out"
  fi
done

echo "logging:"
if [[ -s "$HOME/.claude/hooks/blocked.log" ]]; then
  lines=$(wc -l < "$HOME/.claude/hooks/blocked.log")
  first=$(head -1 "$HOME/.claude/hooks/blocked.log")
  pass=$((pass + 1))
  printf '  ok   blocked.log has %s entries\n         %s\n' "$lines" "$first"
else
  fail=$((fail + 1)); echo "  FAIL blocked.log missing/empty"
fi

echo
echo "passed=$pass failed=$fail"
[[ "$fail" -eq 0 ]]
