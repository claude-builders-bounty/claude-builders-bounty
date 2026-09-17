#!/usr/bin/env bash
# ==============================================================================
# test_hooks.sh — Automated Verification Suite for Claude Code Security Hooks
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_HOOK="${SCRIPT_DIR}/pre_tool_use.py"
BASH_HOOK="${SCRIPT_DIR}/pre-tool-use.sh"

export HOME="${SCRIPT_DIR}/mock_home"
mkdir -p "${HOME}/.claude/hooks"

echo "🧪 Starting Automated Security Hook Verification Suite..."
echo "Mock ~/.claude/hooks: ${HOME}/.claude/hooks"

run_test() {
  local HOOK_EXEC="$1"
  local CMD="$2"
  local EXPECT_BLOCKED="$3"
  local TEST_NAME="$4"

  local EXIT_CODE=0
  "${HOOK_EXEC}" "${CMD}" >/dev/null 2>&1 || EXIT_CODE=$?

  if [ "${EXPECT_BLOCKED}" -eq 1 ]; then
    if [ "${EXIT_CODE}" -ne 0 ]; then
      echo "  ✅ PASS: [BLOCKED] ${TEST_NAME} (\"${CMD}\")"
    else
      echo "  ❌ FAIL: Expected to block but allowed: ${TEST_NAME} (\"${CMD}\")"
      exit 1
    fi
  else
    if [ "${EXIT_CODE}" -eq 0 ]; then
      echo "  ✅ PASS: [ALLOWED] ${TEST_NAME} (\"${CMD}\")"
    else
      echo "  ❌ FAIL: Expected to allow but blocked: ${TEST_NAME} (\"${CMD}\")"
      exit 1
    fi
  fi
}

for RUNNER in "Bash (${BASH_HOOK})" "Python (${PYTHON_HOOK})"; do
  if [[ "${RUNNER}" == *"Bash"* ]]; then
    HOOK_BIN="${BASH_HOOK}"
    chmod +x "${BASH_HOOK}"
  else
    HOOK_BIN="${PYTHON_HOOK}"
    chmod +x "${PYTHON_HOOK}"
  fi

  echo ""
  echo "--- Testing ${RUNNER} ---"

  # Dangerous Commands (MUST BLOCK)
  run_test "${HOOK_BIN}" "rm -rf /tmp/data" 1 "rm -rf standard"
  run_test "${HOOK_BIN}" "rm -fr node_modules" 1 "rm -fr inverted flags"
  run_test "${HOOK_BIN}" "DROP TABLE users;" 1 "DROP TABLE SQL"
  run_test "${HOOK_BIN}" "sqlite3 app.db 'DROP DATABASE prod;'" 1 "DROP DATABASE nested"
  run_test "${HOOK_BIN}" "git push origin main --force" 1 "git push --force"
  run_test "${HOOK_BIN}" "git push -f origin main" 1 "git push -f"
  run_test "${HOOK_BIN}" "TRUNCATE sessions;" 1 "TRUNCATE SQL"
  run_test "${HOOK_BIN}" "TRUNCATE TABLE event_logs;" 1 "TRUNCATE TABLE SQL"
  run_test "${HOOK_BIN}" "DELETE FROM users" 1 "DELETE without WHERE"
  run_test "${HOOK_BIN}" "DELETE FROM accounts; SELECT 1;" 1 "DELETE without WHERE chained"

  # Safe Commands (MUST ALLOW)
  run_test "${HOOK_BIN}" "ls -la" 0 "ls command"
  run_test "${HOOK_BIN}" "git push origin feature-branch" 0 "Safe git push"
  run_test "${HOOK_BIN}" "DELETE FROM users WHERE id = 'user_123'" 0 "DELETE with WHERE"
  run_test "${HOOK_BIN}" "SELECT * FROM users" 0 "SELECT SQL"
  run_test "${HOOK_BIN}" "rm file.txt" 0 "Safe non-recursive rm"
done

# Check log file
LOG_FILE="${HOME}/.claude/hooks/blocked.log"
echo ""
echo "🔍 Checking blocked.log generation..."
if [ -f "${LOG_FILE}" ]; then
  ENTRIES=$(wc -l < "${LOG_FILE}")
  echo "✅ Log file created successfully with ${ENTRIES} audit entries."
  echo "Sample log output:"
  head -n 5 "${LOG_FILE}"
else
  echo "❌ Log file was not created!"
  exit 1
fi

# Cleanup mock directory
rm -rf "${HOME}"
echo ""
echo "🎉 ALL TESTS PASSED SUCCESSFULLY!"
