#!/usr/bin/env bash
# Mirrors .github/workflows/test-claude-review.yml validation steps locally.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
AGENT_DIR="${REPO_ROOT}/agents/claude-review"

cd "$REPO_ROOT"

unit_tests="$(
  grep -Ec '^[[:space:]]*def test_' "${AGENT_DIR}/tests/test_claude_review.py"
)"
python3 -m unittest agents/claude-review/tests/test_claude_review.py -v
echo "Ran ${unit_tests} unit tests — OK"

delivery_tests="$(
  grep -Ec '^[[:space:]]*def test_' "${AGENT_DIR}/tests/test_delivery_verification.py"
)"
python3 -m unittest agents/claude-review/tests/test_delivery_verification.py -v
echo "Ran ${delivery_tests} delivery verification tests — OK"

peer_review_tests="$(
  grep -Ec '^[[:space:]]*def test_' "${AGENT_DIR}/tests/test_peer_review_acceptance.py"
)"
python3 -m unittest agents/claude-review/tests/test_peer_review_acceptance.py -v
echo "Ran ${peer_review_tests} tests — OK"
echo 'OK: peer review acceptance tests passed'

test -x ./claude-review
git diff --check

if grep -rE 'cursoragent@cursor\.com|Made with Cursor|Co-authored-by: Cursor|NEED_CURSOR_HELP' \
  agents/claude-review/ claude-review \
  --exclude-dir=tests; then
  echo 'Forbidden agent attribution strings found in claude-review sources'
  exit 1
fi

if git log -1 --format='%B' | grep -qE \
  'cursoragent@cursor\.com|Made with Cursor|Co-authored-by: Cursor|NEED_CURSOR_HELP'; then
  echo 'Forbidden agent attribution trailer found in HEAD commit message'
  exit 1
fi

git fetch --depth=100 https://github.com/claude-builders-bounty/claude-builders-bounty.git \
  main:refs/remotes/upstream/main 2>/dev/null || true

agent_commit_messages="$(
  git log upstream/main..HEAD --format='%B' -- agents/claude-review/ claude-review 2>/dev/null || true
)"
if printf '%s\n' "$agent_commit_messages" | grep -qE \
  'cursoragent@cursor\.com|Made with Cursor|Co-authored-by: Cursor|NEED_CURSOR_HELP'; then
  echo 'Forbidden agent attribution strings found in agent commit messages'
  exit 1
fi

total_tests=$((unit_tests + delivery_tests + peer_review_tests))
echo "OK: ${total_tests} tests passed"
echo 'OK: all CI validation checks passed'
