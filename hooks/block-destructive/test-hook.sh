#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_PATH="${ROOT_DIR}/pre-tool-use.sh"
TMP_HOME="$(mktemp -d)"
export HOME="${TMP_HOME}"

run_case() {
  local label="$1"
  local payload="$2"
  local output
  local status

  echo "== ${label} =="
  output="$(printf '%s' "${payload}" | "${HOOK_PATH}" 2>&1)"
  status=$?

  if [[ ${status} -eq 0 ]] && printf '%s' "${output}" | rg -q '"permissionDecision"\s*:\s*"deny"'; then
    echo "blocked"
  elif [[ ${status} -eq 0 ]]; then
    echo "allowed"
  else
    echo "blocked"
  fi
  if [[ -n "${output}" ]]; then
    echo "${output}"
  fi
  echo
}

run_case \
  "safe command" \
  '{"tool_name":"Bash","tool_input":{"command":"echo safe","cwd":"/tmp/demo"}}'

run_case \
  "rm -rf" \
  '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/demo","cwd":"/tmp/demo"}}'

run_case \
  "delete from without where" \
  '{"tool_name":"Bash","tool_input":{"command":"psql -c \"DELETE FROM users;\"","cwd":"/tmp/demo"}}'

run_case \
  "git push --force" \
  '{"tool_name":"Bash","tool_input":{"command":"git push --force origin main","cwd":"/tmp/demo"}}'

echo "Blocked log:"
cat "${HOME}/.claude/hooks/blocked.log"
