#!/usr/bin/env bash
# Unified local/CI validation for issue #521 README bounty table links (PR #2532).
# Mirrors .github/workflows/test-readme-links.yml — run via `npm test` or `make test`.
set -euo pipefail
set +x

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ATTRIBUTION_PATTERN='cursoragent@cursor\.com|Made with Cursor|Co-authored-by: Cursor|NEED_CURSOR_HELP'

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
  if ! git show-ref -q refs/heads/main >/dev/null 2>&1; then
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

attribution_scan_files=(
  README.md
  tests/test_readme_links.py
  tests/test_peer_review_acceptance.py
  tests/test_delivery_verification.py
  .github/workflows/test-readme-links.yml
)

if git show-ref -q refs/heads/main >/dev/null 2>&1; then
  while IFS= read -r changed_file; do
  [[ -z "${changed_file}" ]] && continue
  [[ "${changed_file}" == "tests/run-ci-checks.sh" ]] && continue
  attribution_scan_files+=("${changed_file}")
  done < <(git diff --name-only main...HEAD 2>/dev/null || git diff --name-only main..HEAD)
fi

declare -A attribution_seen=()
for scan_file in "${attribution_scan_files[@]}"; do
  [[ -z "${scan_file}" ]] && continue
  [[ -n "${attribution_seen["${scan_file}"]:-}" ]] && continue
  attribution_seen["${scan_file}"]=1
  [[ ! -f "${REPO_ROOT}/${scan_file}" ]] && continue
  if grep -qE "${ATTRIBUTION_PATTERN}" "${REPO_ROOT}/${scan_file}"; then
    echo "Forbidden agent attribution strings found in ${scan_file}"
    exit 1
  fi
done

if git log -1 --format='%B' | grep -qE "${ATTRIBUTION_PATTERN}"; then
  echo 'Forbidden agent attribution trailer found in HEAD commit message'
  exit 1
fi

if git log -1 --format='%ae%n%ce' | grep -qF 'cursoragent@cursor.com'; then
  echo 'Forbidden agent attribution email found in HEAD commit'
  exit 1
fi

if git show-ref -q refs/heads/main >/dev/null 2>&1; then
  while IFS= read -r commit_msg; do
    [[ -z "${commit_msg}" ]] && continue
    if printf '%s' "${commit_msg}" | grep -qE "${ATTRIBUTION_PATTERN}"; then
      echo 'Forbidden agent attribution trailer found in branch commit message'
      exit 1
    fi
  done < <(git log --format='%B' main..HEAD 2>/dev/null || true)
fi

echo 'OK: all CI validation checks passed'
