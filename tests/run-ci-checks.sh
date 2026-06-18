#!/usr/bin/env bash
# Unified local/CI validation for issue #521 README bounty table links (PR #2532).
# Mirrors .github/workflows/test-readme-links.yml — run via `npm test` or `make test`.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$REPO_ROOT"

# --- Stage 1: README link regression (tests/test_readme_links.py) ---
readme_link_tests="$(
  grep -Ec '^[[:space:]]*def test_' "${REPO_ROOT}/tests/test_readme_links.py"
)"
python3 -m unittest tests/test_readme_links.py -v
echo "Ran ${readme_link_tests} README link tests — OK"

# --- Stage 2: Peer-review acceptance (tests/test_peer_review_acceptance.py) ---
peer_review_tests="$(
  grep -Ec '^[[:space:]]*def test_' "${REPO_ROOT}/tests/test_peer_review_acceptance.py"
)"
python3 -m unittest tests/test_peer_review_acceptance.py -v
echo "Ran ${peer_review_tests} peer review acceptance tests — OK"
echo 'OK: peer review acceptance tests passed'

# --- Stage 3: Delivery verification (skipped when invoked from npm test inner run) ---
if [[ -z "${README_CI_INNER_RUN:-}" ]]; then
  if ! git rev-parse --verify main >/dev/null 2>&1; then
    git fetch --no-tags --depth 50 origin main:main
  fi

  delivery_tests="$(
    grep -Ec '^[[:space:]]*def test_' "${REPO_ROOT}/tests/test_delivery_verification.py"
  )"
  python3 -m unittest tests/test_delivery_verification.py -v
  echo "Ran ${delivery_tests} delivery verification tests — OK"
  echo 'OK: delivery verification tests passed'
fi

# --- Stage 4: Repo hygiene (whitespace, forbidden agent attribution) ---
git diff --check

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
