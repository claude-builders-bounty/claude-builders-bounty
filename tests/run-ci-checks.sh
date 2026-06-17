#!/usr/bin/env bash
# Mirrors .github/workflows/test-readme-links.yml validation steps locally.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$REPO_ROOT"

readme_link_tests="$(
  grep -Ec '^[[:space:]]*def test_' "${REPO_ROOT}/tests/test_readme_links.py"
)"
python3 -m unittest tests/test_readme_links.py -v
echo "Ran ${readme_link_tests} README link tests — OK"

peer_review_tests="$(
  grep -Ec '^[[:space:]]*def test_' "${REPO_ROOT}/tests/test_peer_review_acceptance.py"
)"
python3 -m unittest tests/test_peer_review_acceptance.py -v
echo "Ran ${peer_review_tests} peer review acceptance tests — OK"
echo 'OK: peer review acceptance tests passed'

issue_2853_tests="$(
  grep -Ec '^[[:space:]]*def test_' "${REPO_ROOT}/tests/test_issue_2853_read_tool_hook.py"
)"
python3 -m unittest tests/test_issue_2853_read_tool_hook.py -v
echo "Ran ${issue_2853_tests} issue #2853 read tool hook acceptance tests — OK"
echo 'OK: issue #2853 read tool hook acceptance tests passed'

if [[ -z "${README_CI_INNER_RUN:-}" ]]; then
  if ! git rev-parse --verify main >/dev/null 2>&1; then
    git fetch --no-tags --depth 50 origin main:main
  fi

  delivery_tests="$(
    grep -Ec '^[[:space:]]*def test_' "${REPO_ROOT}/tests/test_delivery_verification.py"
  )"
  python3 -m unittest tests/test_delivery_verification.py -v
  echo "Ran ${delivery_tests} delivery verification tests — OK"
fi

# Scan CI-guarded files for trailing whitespace (scoped find/grep, not full-repo git diff).
_whitespace_fail=0
while IFS= read -r -d '' _ws_file; do
  if grep -n '[[:space:]]$' "$_ws_file" >/dev/null 2>&1; then
    echo "trailing whitespace in ${_ws_file}"
    _whitespace_fail=1
  fi
done < <(
  find tests README.md package.json Makefile .github/workflows \
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
