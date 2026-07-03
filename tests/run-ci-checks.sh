#!/usr/bin/env bash
# Validates README bounty table issue links for PR #2846 / issue #2746.
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

git diff --check

if grep -rE 'cursoragent@cursor\.com|Made with Cursor|Co-authored-by: Cursor|NEED_CURSOR_HELP' \
  README.md tests/test_readme_links.py tests/test_peer_review_acceptance.py \
  .github/workflows/test-readme-links.yml; then
  echo 'Forbidden agent attribution strings found in README link sources'
  exit 1
fi

commit_msg="$(git log -1 --format='%B')"
if echo "$commit_msg" | grep -qE \
  'cursoragent@cursor\.com|Made with Cursor|Co-authored-by: Cursor|NEED_CURSOR_HELP'; then
  echo 'Forbidden agent attribution trailer found in HEAD commit message'
  exit 1
fi

# Reject likely secrets in the latest commit message (API keys, tokens, passwords).
if echo "$commit_msg" | grep -qiE \
  '(api[_-]?key|secret|password|token|bearer)[[:space:]:=]+[[:alnum:]_-]{8,}|'\
'sk-[[:alnum:]]{10,}|'\
'ghp_[[:alnum:]]{20,}|'\
'gho_[[:alnum:]]{20,}|'\
'AKIA[0-9A-Z]{16}|'\
'-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----'; then
  echo 'Sensitive information pattern found in HEAD commit message'
  exit 1
fi

if git log -1 --format='%ae%n%ce' | grep -qF 'cursoragent@cursor.com'; then
  echo 'Forbidden agent attribution email found in HEAD commit'
  exit 1
fi

echo 'OK: all CI validation checks passed'
