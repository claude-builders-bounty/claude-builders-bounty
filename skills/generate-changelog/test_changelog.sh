#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT

cd "$workdir"
git init -q
git config user.email "changelog-test@example.com"
git config user.name "Changelog Test"

printf 'one\n' > app.txt
git add app.txt
git commit -q -m "feat: add app shell"

git tag v0.1.0

printf 'two\n' >> app.txt
git add app.txt
git commit -q -m "fix: handle empty input"

printf 'docs\n' > README.md
git add README.md
git commit -q -m "docs: update usage notes"

printf 'old\n' > old.txt
git add old.txt
git commit -q -m "remove: drop legacy fixture"

"$script_dir/changelog.sh" > result.txt

grep -q 'Range: v0.1.0..HEAD' result.txt
grep -q 'Generated CHANGELOG.md from 3 commits.' result.txt
grep -q -- '- handle empty input' CHANGELOG.md
grep -q -- '- update usage notes' CHANGELOG.md
grep -q -- '- drop legacy fixture' CHANGELOG.md

if grep -q 'add app shell' CHANGELOG.md; then
  echo "tagged commit leaked into generated changelog" >&2
  exit 1
fi

echo "generate-changelog smoke test passed"
