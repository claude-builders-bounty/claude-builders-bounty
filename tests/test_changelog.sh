#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

git -C "$WORK_DIR" init -q
git -C "$WORK_DIR" config user.name "Changelog Test"
git -C "$WORK_DIR" config user.email "test@example.com"

printf 'initial\n' >"$WORK_DIR/app.txt"
git -C "$WORK_DIR" add app.txt
git -C "$WORK_DIR" commit -q -m "feat: initial release"
git -C "$WORK_DIR" tag v1.0.0

printf 'new endpoint\n' >>"$WORK_DIR/app.txt"
git -C "$WORK_DIR" add app.txt
git -C "$WORK_DIR" commit -q -m "feat(api): add export endpoint"

printf 'bug fix\n' >>"$WORK_DIR/app.txt"
git -C "$WORK_DIR" add app.txt
git -C "$WORK_DIR" commit -q -m "fix: handle empty history"

printf 'refactor\n' >>"$WORK_DIR/app.txt"
git -C "$WORK_DIR" add app.txt
git -C "$WORK_DIR" commit -q -m "refactor: simplify parser"

git -C "$WORK_DIR" rm -q app.txt
git -C "$WORK_DIR" commit -q -m "remove obsolete fixture"

bash "$REPO_ROOT/scripts/changelog.sh" --repo "$WORK_DIR" --output "$WORK_DIR/CHANGELOG.md" --version 1.1.0

grep -q 'Generated from commits since `v1.0.0`' "$WORK_DIR/CHANGELOG.md"
grep -q '### Added' "$WORK_DIR/CHANGELOG.md"
grep -q 'add export endpoint' "$WORK_DIR/CHANGELOG.md"
grep -q '### Fixed' "$WORK_DIR/CHANGELOG.md"
grep -q 'handle empty history' "$WORK_DIR/CHANGELOG.md"
grep -q '### Changed' "$WORK_DIR/CHANGELOG.md"
grep -q 'simplify parser' "$WORK_DIR/CHANGELOG.md"
grep -q '### Removed' "$WORK_DIR/CHANGELOG.md"
grep -q 'obsolete fixture' "$WORK_DIR/CHANGELOG.md"

if grep -q 'initial release' "$WORK_DIR/CHANGELOG.md"; then
  echo "pre-tag commit leaked into generated changelog" >&2
  exit 1
fi

echo "test_changelog.sh passed"
