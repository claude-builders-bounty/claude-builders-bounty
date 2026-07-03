#!/usr/bin/env bash
# Mirrors .github/workflows/test-block-destructive-commands.yml validation steps locally.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
HOOK_DIR="${REPO_ROOT}/hooks/block-destructive-commands"

cd "$REPO_ROOT"

python3 -m unittest discover -s "${HOOK_DIR}/tests" -v

delivery_tests="$(
  grep -Ec '^[[:space:]]*def test_' "${HOOK_DIR}/tests/test_delivery_verification.py"
)"
python3 -m unittest "${HOOK_DIR}/tests/test_delivery_verification.py" -v
echo "Ran ${delivery_tests} delivery verification tests — OK"

peer_review_tests="$(
  grep -Ec '^[[:space:]]*def test_' "${HOOK_DIR}/tests/test_peer_review_acceptance.py"
)"
python3 -m unittest "${HOOK_DIR}/tests/test_peer_review_acceptance.py" -v
echo "Ran ${peer_review_tests} tests — OK"
echo 'OK: peer review acceptance tests passed'

git diff --check

if grep -rE 'cursoragent@cursor\.com|Made with Cursor|Co-authored-by: Cursor|NEED_CURSOR_HELP' \
  "${HOOK_DIR}/pre-tool-use.py" "${HOOK_DIR}/install.sh" "${HOOK_DIR}/README.md" \
  "${HOOK_DIR}/settings.json"; then
  echo 'Forbidden agent attribution strings found in hook sources'
  exit 1
fi

if git log -1 --format='%B' | grep -qE \
  'cursoragent@cursor\.com|Made with Cursor|Co-authored-by: Cursor|NEED_CURSOR_HELP'; then
  echo 'Forbidden agent attribution trailer found in HEAD commit message'
  exit 1
fi

if git log -1 --format='%ae%n%ce' | grep -qF 'cursoragent@cursor.com'; then
  echo 'Forbidden agent attribution email found in HEAD commit'
  exit 1
fi

echo 'OK: all CI validation checks passed'
