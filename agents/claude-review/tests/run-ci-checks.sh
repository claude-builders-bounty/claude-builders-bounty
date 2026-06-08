#!/usr/bin/env bash
# Mirrors .github/workflows/test-claude-review.yml validation steps locally.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

cd "$REPO_ROOT"

python3 -m unittest agents/claude-review/tests/test_claude_review.py -v
python3 -m unittest agents/claude-review/tests/test_peer_review_acceptance.py -v
echo 'OK: peer review acceptance tests passed'
test -x ./claude-review
git diff --check

if grep -rE 'cursoragent@cursor\.com|Made with Cursor|Co-authored-by: Cursor' \
  agents/claude-review/ claude-review \
  --exclude-dir=tests; then
  echo 'Forbidden agent attribution strings found in claude-review sources'
  exit 1
fi

git fetch --depth=100 https://github.com/claude-builders-bounty/claude-builders-bounty.git \
  main:refs/remotes/upstream/main 2>/dev/null || true

if git log upstream/main..HEAD --format='%B' 2>/dev/null | \
  grep -qE 'cursoragent@cursor\.com|Made with Cursor|Co-authored-by: Cursor'; then
  echo 'Forbidden agent attribution strings found in PR commit messages'
  exit 1
fi

echo 'OK: all CI validation checks passed'
