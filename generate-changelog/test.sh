#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

cp "$repo_root/changelog.sh" "$tmp/changelog.sh"
mkdir -p "$tmp/generate-changelog"
cp "$repo_root/generate-changelog/changelog.sh" "$tmp/generate-changelog/changelog.sh"

(
  cd "$tmp"
  git init -q
  git config user.name "Changelog Test"
  git config user.email "changelog-test@example.com"

  echo "one" > file.txt
  git add file.txt
  git commit -qm "feat: initial feature"
  git tag v0.1.0

  echo "two" >> file.txt
  git add file.txt
  git commit -qm "fix: repair output"

  echo "three" >> file.txt
  git add file.txt
  git commit -qm "remove: old path"

  echo "four" >> file.txt
  git add file.txt
  git commit -qm "feat(api)!: scoped breaking feature"

  echo "five" >> file.txt
  git add file.txt
  git commit -qm "fix(core): scoped bug fix"

  echo "six" >> file.txt
  git add file.txt
  git commit -qm "docs(readme): scoped docs update"

  bash ./changelog.sh OUT.md >/dev/null

  grep -q "Generated from git history since v0.1.0" OUT.md
  grep -q "### Added" OUT.md
  grep -q "scoped breaking feature" OUT.md
  grep -q "### Fixed" OUT.md
  grep -q "repair output" OUT.md
  grep -q "scoped bug fix" OUT.md
  grep -q "### Changed" OUT.md
  grep -q "scoped docs update" OUT.md
  grep -q "### Removed" OUT.md
  grep -q "old path" OUT.md
  if grep -q "initial feature" OUT.md; then
    echo "test failed: included commit before latest tag" >&2
    exit 1
  fi
)

echo "generate-changelog tests passed"
