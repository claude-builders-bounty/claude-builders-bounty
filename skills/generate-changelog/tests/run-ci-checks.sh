#!/usr/bin/env bash
# Mirrors .github/workflows/test-changelog.yml validation steps locally.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SKILL_DIR="${REPO_ROOT}/skills/generate-changelog"

cd "$REPO_ROOT"

bash "${SKILL_DIR}/tests/test_changelog.sh"

peer_review_tests="$(
  grep -Ec '^[[:space:]]*def test_' "${SKILL_DIR}/tests/test_peer_review_acceptance.py"
)"
python3 -m unittest "${SKILL_DIR}/tests/test_peer_review_acceptance.py" -v
echo "Ran ${peer_review_tests} tests — OK"
echo 'OK: peer review acceptance tests passed'

preview="$(mktemp)"
sample="$(mktemp)"
bash changelog.sh --preview 2>/dev/null >"$preview"
preview_body="${preview}.body"
sample_body="${sample}.body"
grep -v '^## \[.*\] - ' "$preview" >"$preview_body"
last_sample_commit="$(git log -1 --format=%H -- skills/generate-changelog/samples/CHANGELOG.sample.md || true)"
if [[ -n "$last_sample_commit" ]]; then
  while IFS= read -r hash; do
    short_hash="$(git rev-parse --short "$hash")"
    grep -v "(${short_hash})" "$preview_body" >"${preview_body}.trim"
    mv "${preview_body}.trim" "$preview_body"
  done < <(git rev-list "${last_sample_commit}^..HEAD" 2>/dev/null || git rev-list "${last_sample_commit}..HEAD" 2>/dev/null || true)
fi
grep -v '^## \[.*\] - ' skills/generate-changelog/samples/CHANGELOG.sample.md >"$sample_body"
diff -u "$sample_body" "$preview_body"

git diff --check

if grep -rE 'cursoragent@cursor\.com|Made with Cursor|Co-authored-by: Cursor' \
  skills/generate-changelog/ changelog.sh \
  --exclude-dir=tests; then
  echo 'Forbidden agent attribution strings found in changelog sources'
  exit 1
fi

git fetch --depth=100 https://github.com/claude-builders-bounty/claude-builders-bounty.git \
  main:refs/remotes/upstream/main 2>/dev/null || true

if git log -1 --format='%B' | grep -qE 'cursoragent@cursor\.com|Made with Cursor|Co-authored-by: Cursor'; then
  echo 'Forbidden agent attribution trailer found in HEAD commit message'
  exit 1
fi

if git log -1 --format='%ae%n%ce' | grep -qF 'cursoragent@cursor.com'; then
  echo 'Forbidden agent attribution email found in HEAD commit'
  exit 1
fi

echo 'OK: all CI validation checks passed'
