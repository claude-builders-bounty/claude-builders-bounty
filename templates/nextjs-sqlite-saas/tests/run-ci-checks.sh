#!/usr/bin/env bash
# Mirrors .github/workflows/test-nextjs-sqlite-template.yml validation steps locally.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TEMPLATE_DIR="${REPO_ROOT}/templates/nextjs-sqlite-saas"

cd "$REPO_ROOT"

node "${TEMPLATE_DIR}/validate-template.mjs"
bash "${TEMPLATE_DIR}/tests/smoke-greenfield.sh"

peer_review_tests="$(
  grep -Ec '^\s*assert\(' "${TEMPLATE_DIR}/tests/peer-review-acceptance.test.mjs"
)"
node "${TEMPLATE_DIR}/tests/peer-review-acceptance.test.mjs"
echo "Ran ${peer_review_tests} tests — OK"
echo 'OK: peer review acceptance tests passed'

git diff --check

if grep -rE 'cursoragent@cursor\.com|Made with Cursor|Co-authored-by: Cursor|NEED_CURSOR_HELP' \
  "${TEMPLATE_DIR}/" \
  --exclude-dir=tests; then
  echo 'Forbidden agent attribution strings found in template sources'
  exit 1
fi

git fetch --depth=100 https://github.com/claude-builders-bounty/claude-builders-bounty.git \
  main:refs/remotes/upstream/main 2>/dev/null || true

template_commit_messages="$(
  git log upstream/main..HEAD --format='%B' -- templates/nextjs-sqlite-saas/ 2>/dev/null || true
)"
if printf '%s\n' "$template_commit_messages" | grep -qE \
  'cursoragent@cursor\.com|Made with Cursor|Co-authored-by: Cursor|NEED_CURSOR_HELP'; then
  echo 'Forbidden agent attribution strings found in template commit messages'
  exit 1
fi

echo 'OK: all CI validation checks passed'
