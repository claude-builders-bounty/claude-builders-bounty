#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
script="$repo_root/changelog.sh"
tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

cd "$tmpdir"
git init >/dev/null
git config user.name "Changelog Test"
git config user.email "test@example.com"

printf 'one\n' > file.txt
git add file.txt
git commit -m "feat: initial feature" >/dev/null
git tag v1.0.0

printf 'two\n' >> file.txt
git commit -am "fix: repair issue" >/dev/null

printf 'three\n' >> file.txt
git commit -am "remove: old behavior" >/dev/null

bash "$script" --output CHANGELOG.md --no-links >/dev/null

grep -Fq 'Generated from git history since `v1.0.0`.' CHANGELOG.md
grep -Fq '### Fixed' CHANGELOG.md
grep -Fq 'fix: repair issue' CHANGELOG.md
grep -Fq '### Removed' CHANGELOG.md
grep -Fq 'remove: old behavior' CHANGELOG.md

if grep -Fq 'feat: initial feature' CHANGELOG.md; then
  echo "Expected changelog to exclude commits before the latest tag" >&2
  exit 1
fi

echo "test_changelog.sh passed"
