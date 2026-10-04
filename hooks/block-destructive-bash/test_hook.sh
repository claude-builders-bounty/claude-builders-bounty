#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
HOOK="$ROOT/block_destructive.py"
LOG="${HOME}/.claude/hooks/blocked.log"
TEST_LOG="/tmp/bounty-work/hook3/test-blocked.log"
PROJECT="/tmp/bounty-work/hook3/sample-project"

mkdir -p "$(dirname "$LOG")" "$PROJECT"
: > "$TEST_LOG"
export LOG_PATH="$TEST_LOG"
# Hook uses fixed path; run tests with a symlink trick — patch via env not supported.
# Tests use real LOG_PATH in hook; backup and restore blocked.log.
BACKUP=""
if [[ -f "$LOG" ]]; then
  BACKUP="$(mktemp)"
  cp "$LOG" "$BACKUP"
fi
: > "$LOG"

run_case() {
  local name="$1"
  local expect="$2"
  local payload="$3"
  set +e
  out=$(echo "$payload" | python3 "$HOOK" 2>&1)
  code=$?
  set -e
  if [[ "$expect" == "block" && "$code" -ne 2 ]]; then
    echo "FAIL $name: expected exit 2, got $code"
    echo "$out"
    return 1
  fi
  if [[ "$expect" == "allow" && "$code" -ne 0 ]]; then
    echo "FAIL $name: expected exit 0, got $code"
    echo "$out"
    return 1
  fi
  echo "PASS $name (exit $code)"
}

payload() {
  local cmd="$1"
  python3 -c 'import json,sys; print(json.dumps({"tool_name":"Bash","cwd":sys.argv[1],"tool_input":{"command":sys.argv[2]}}))' "$PROJECT" "$cmd"
}

FAIL=0
block_cmds=(
  "rm -rf /tmp/foo"
  "cd /x && rm -rf ."
  "mysql -e 'DROP TABLE users'"
  "git push --force origin main"
  "psql -c 'TRUNCATE logs'"
  "sqlite3 db.sqlite \"DELETE FROM users\""
)
for c in "${block_cmds[@]}"; do
  run_case "block: $c" block "$(payload "$c")" || FAIL=1
done

allow_cmds=(
  "ls -la"
  "git status"
  "echo hello"
  "grep foo bar.txt"
  "rm -r single_dir"
  "git push origin main"
  "sqlite3 db.sqlite \"DELETE FROM users WHERE id=1\""
)
for c in "${allow_cmds[@]}"; do
  run_case "allow: $c" allow "$(payload "$c")" || FAIL=1
done

echo "--- blocked.log ---"
cat "$LOG"
echo "--- log line check ---"
if [[ "$(wc -l < "$LOG" | tr -d ' ')" -ne "${#block_cmds[@]}" ]]; then
  echo "FAIL: expected ${#block_cmds[@]} log lines, got $(wc -l < "$LOG")"
  FAIL=1
else
  echo "PASS: log line count"
fi
if ! head -1 "$LOG" | grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2}T.*project=.*/sample-project.*command='; then
  echo "FAIL: log format"
  FAIL=1
else
  echo "PASS: log format (timestamp, project, command)"
fi

if [[ -n "$BACKUP" ]]; then
  mv "$BACKUP" "$LOG"
else
  rm -f "$LOG"
fi

if [[ "$FAIL" -ne 0 ]]; then
  echo "Some tests failed."
  exit 1
fi
echo "All tests passed."
