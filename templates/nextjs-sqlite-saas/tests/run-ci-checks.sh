#!/usr/bin/env bash
# Mirrors .github/workflows/test-nextjs-sqlite-template.yml validation steps locally.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TEMPLATE_DIR="${REPO_ROOT}/templates/nextjs-sqlite-saas"

cd "$REPO_ROOT"

ensure_git_base_ref() {
  if ! git rev-parse --verify upstream/main >/dev/null 2>&1; then
    git fetch --depth=100 https://github.com/claude-builders-bounty/claude-builders-bounty.git \
      main:refs/remotes/upstream/main 2>/dev/null || true
  fi
  if ! git merge-base upstream/main HEAD >/dev/null 2>&1; then
    git fetch --deepen=500 origin 2>/dev/null || \
      git fetch --deepen=500 https://github.com/claude-builders-bounty/claude-builders-bounty.git \
        main:refs/remotes/upstream/main 2>/dev/null || true
  fi
}

ensure_git_base_ref

node "${TEMPLATE_DIR}/validate-template.mjs"
bash "${TEMPLATE_DIR}/tests/smoke-greenfield.sh"

delivery_verification_tests="$(
  grep -Ec '^test\(' "${TEMPLATE_DIR}/tests/delivery-verification.test.mjs"
)"
node "${TEMPLATE_DIR}/tests/delivery-verification.test.mjs"
echo "Ran ${delivery_verification_tests} delivery verification tests — OK"

peer_review_tests="$(
  grep -Ec '^\s*assert\(' "${TEMPLATE_DIR}/tests/peer-review-acceptance.test.mjs"
)"
node "${TEMPLATE_DIR}/tests/peer-review-acceptance.test.mjs"
echo "Ran ${peer_review_tests} tests — OK"
echo 'OK: peer review acceptance tests passed'
total_tests=$((delivery_verification_tests + peer_review_tests))
echo "OK: ${total_tests} tests passed"

git diff --check

if grep -rE 'cursoragent@cursor\.com|Made with Cursor|Co-authored-by: Cursor|NEED_CURSOR_HELP' \
  "${TEMPLATE_DIR}/" \
  --exclude-dir=tests; then
  echo 'Forbidden agent attribution strings found in template sources'
  exit 1
fi

if git log -1 --format='%B' | grep -qE \
  'cursoragent@cursor\.com|Made with Cursor|Co-authored-by: Cursor|NEED_CURSOR_HELP'; then
  echo 'Forbidden agent attribution trailer found in HEAD commit message'
  exit 1
fi

template_commit_messages="$(
  git log upstream/main..HEAD --format='%B' -- templates/nextjs-sqlite-saas/ 2>/dev/null || true
)"
if printf '%s\n' "$template_commit_messages" | grep -qE \
  'cursoragent@cursor\.com|Made with Cursor|Co-authored-by: Cursor|NEED_CURSOR_HELP'; then
  echo 'Forbidden agent attribution strings found in template commit messages'
  exit 1
fi

echo 'OK: all CI validation checks passed'
