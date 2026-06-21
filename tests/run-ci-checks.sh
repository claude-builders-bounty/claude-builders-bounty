#!/usr/bin/env bash
# Mirrors .github/workflows/test-readme-links.yml validation steps locally.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_MODULE="${REPO_ROOT}/tests/run-unittest-module.sh"

cd "$REPO_ROOT"

bash "$RUN_MODULE" tests/test_readme_links.py "README link tests"

bash "$RUN_MODULE" tests/test_peer_review_acceptance.py "peer review acceptance tests" \
  "OK: peer review acceptance tests passed"

bash "$RUN_MODULE" tests/test_issue_2853_read_tool_hook.py "issue #2853 read tool hook acceptance tests" \
  "OK: issue #2853 read tool hook acceptance tests passed"

if [[ -z "${README_CI_INNER_RUN:-}" ]]; then
  if ! git rev-parse --verify main >/dev/null 2>&1; then
    git fetch --no-tags --depth 50 origin main:main
  fi

  bash "$RUN_MODULE" tests/test_delivery_verification.py "delivery verification tests"
fi

# Scan security-critical CI paths for trailing whitespace (scoped find/grep, not full-repo diff).
# Peer review #2871: scope to tests/, package.json, and .github/workflows/ (+ Makefile/README).
_CI_GUARDED_PATHS=(
  tests
  package.json
  .github/workflows
  Makefile
  README.md
)
_whitespace_fail=0
while IFS= read -r -d '' _ws_file; do
  if grep -n '[[:space:]]$' "$_ws_file" >/dev/null 2>&1; then
    echo "trailing whitespace in ${_ws_file}"
    _whitespace_fail=1
  fi
done < <(
  find "${_CI_GUARDED_PATHS[@]}" \
    -type f \( -name '*.py' -o -name '*.sh' -o -name '*.md' -o -name '*.json' \
      -o -name '*.yml' -o -name 'Makefile' \) \
    -print0 2>/dev/null
)
if [[ "$_whitespace_fail" -ne 0 ]]; then
  exit 1
fi

if grep -rE 'cursoragent@cursor\.com|Made with Cursor|Co-authored-by: Cursor|NEED_CURSOR_HELP' \
  README.md tests/test_readme_links.py tests/test_peer_review_acceptance.py \
  .github/workflows/test-readme-links.yml; then
  echo 'Forbidden agent attribution strings found in README link sources'
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
