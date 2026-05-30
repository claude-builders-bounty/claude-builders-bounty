#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK="${SCRIPT_DIR}/pre_tool_use_guard.py"
TMP_HOME="$(mktemp -d)"
export HOME="${TMP_HOME}"
if command -v cygpath >/dev/null 2>&1; then
  export USERPROFILE="$(cygpath -w "${TMP_HOME}")"
else
  export USERPROFILE="${TMP_HOME}"
fi

failures=0
PYTHON_CMD=()

detect_python() {
  if [[ -n "${PYTHON_BIN:-}" ]] && "${PYTHON_BIN}" --version >/dev/null 2>&1; then
    PYTHON_CMD=("${PYTHON_BIN}")
    return 0
  fi
  if command -v python3 >/dev/null 2>&1 && python3 --version >/dev/null 2>&1; then
    PYTHON_CMD=(python3)
    return 0
  fi
  if command -v python >/dev/null 2>&1 && python --version >/dev/null 2>&1; then
    PYTHON_CMD=(python)
    return 0
  fi
  if command -v py >/dev/null 2>&1 && py -3 --version >/dev/null 2>&1; then
    PYTHON_CMD=(py -3)
    return 0
  fi
  return 1
}

if ! detect_python; then
  echo "Could not find Python. Set PYTHON_BIN=/path/to/python and rerun." >&2
  exit 1
fi

run_case() {
  local name="$1"
  local command="$2"
  local expected="$3"
  local payload
  local output
  local status

  payload="$("${PYTHON_CMD[@]}" - "$command" <<'PY'
import json
import sys

print(json.dumps({
    "tool_name": "Bash",
    "cwd": "/tmp/pretooluse-test",
    "tool_input": {"command": sys.argv[1]},
}))
PY
)"

  output="$(printf '%s\n' "$payload" | "${PYTHON_CMD[@]}" "$HOOK" 2>&1)"
  status=$?

  if [[ "$status" -ne "$expected" ]]; then
    printf 'not ok - %s: expected exit %s, got %s\n%s\n' "$name" "$expected" "$status" "$output"
    failures=$((failures + 1))
    return
  fi

  printf 'ok - %s\n' "$name"
}

run_case "safe git status" "git status --short" 0
run_case "safe delete with where" "DELETE FROM users WHERE id = 1;" 0
run_case "blocks rm -rf" "rm -rf dist" 2
run_case "blocks rm -fr" "rm -fr dist" 2
run_case "blocks drop table" "psql -c 'DROP TABLE users;'" 2
run_case "blocks force push" "git push --force origin main" 2
run_case "blocks force-with-lease" "git push --force-with-lease origin main" 2
run_case "blocks truncate" "TRUNCATE sessions;" 2
run_case "blocks delete without where" "DELETE FROM users;" 2

LOG_FILE="${TMP_HOME}/.claude/hooks/blocked.log"
if [[ ! -f "$LOG_FILE" ]]; then
  printf 'not ok - blocked.log was not created\n'
  failures=$((failures + 1))
else
  blocked_lines="$(wc -l < "$LOG_FILE" | tr -d ' ')"
  if [[ "$blocked_lines" -ne 7 ]]; then
    printf 'not ok - expected 7 blocked log lines, got %s\n' "$blocked_lines"
    failures=$((failures + 1))
  else
    printf 'ok - blocked attempts logged\n'
  fi
fi

rm -rf "$TMP_HOME"

if [[ "$failures" -ne 0 ]]; then
  exit 1
fi

exit 0
