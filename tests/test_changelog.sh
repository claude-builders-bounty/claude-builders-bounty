#!/usr/bin/env bash
set -euo pipefail

repo="$(mktemp -d)"
trap 'rm -rf "$repo"' EXIT

git -C "$repo" init -q
git -C "$repo" config user.name "Test"
git -C "$repo" config user.email "test@example.com"

echo "one" >"$repo/file.txt"
git -C "$repo" add file.txt
git -C "$repo" commit -q -m "feat: initial feature"
git -C "$repo" tag v1.0.0

echo "two" >>"$repo/file.txt"
git -C "$repo" commit -q -am "fix: repair parser"

echo "three" >>"$repo/file.txt"
git -C "$repo" commit -q -am "docs: update usage"

echo "four" >>"$repo/file.txt"
git -C "$repo" commit -q -am "remove: old option"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
(cd "$repo" && bash "$script_dir/changelog/changelog.sh" CHANGELOG.md)

grep -q "Changes since \`v1.0.0\`" "$repo/CHANGELOG.md"
grep -q "Repair parser" "$repo/CHANGELOG.md"
grep -q "Update usage" "$repo/CHANGELOG.md"
grep -q "Old option" "$repo/CHANGELOG.md"
if grep -q "Initial feature" "$repo/CHANGELOG.md"; then
  echo "tagged commit should not appear in changelog" >&2
  exit 1
fi
