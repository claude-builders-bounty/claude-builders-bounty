#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
test_repo="$(mktemp -d)"
trap 'rm -rf "$test_repo"' EXIT

git -C "$test_repo" init -q
git -C "$test_repo" config user.email test@example.com
git -C "$test_repo" config user.name "Changelog Test"

printf 'initial\n' > "$test_repo/example.txt"
git -C "$test_repo" add example.txt
git -C "$test_repo" commit -qm 'feat: add initial example'
git -C "$test_repo" tag v1.0.0

printf 'fixed\n' > "$test_repo/example.txt"
git -C "$test_repo" add example.txt
git -C "$test_repo" commit -qm 'fix: handle empty input'

printf 'feature\n' >> "$test_repo/example.txt"
git -C "$test_repo" add example.txt
git -C "$test_repo" commit -qm 'feat(parser): support scoped prefixes'

printf 'docs\n' > "$test_repo/README.md"
git -C "$test_repo" add README.md
git -C "$test_repo" commit -qm 'docs: explain usage'

(cd "$test_repo" && bash "$script_dir/changelog.sh" "$test_repo/CHANGELOG.md") >/dev/null

grep -Fq '## [Unreleased]' "$test_repo/CHANGELOG.md"
grep -Fq '### Fixed' "$test_repo/CHANGELOG.md"
grep -Fq 'handle empty input' "$test_repo/CHANGELOG.md"
grep -Fq '### Added' "$test_repo/CHANGELOG.md"
grep -Fq 'support scoped prefixes' "$test_repo/CHANGELOG.md"
grep -Fq '### Changed' "$test_repo/CHANGELOG.md"
grep -Fq 'explain usage' "$test_repo/CHANGELOG.md"
if grep -Fq 'add initial example' "$test_repo/CHANGELOG.md"; then
  printf 'Tagged commits must not appear in the generated range.\n' >&2
  exit 1
fi

printf 'All changelog tests passed.\n'
