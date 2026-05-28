#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

FIXTURE="$TMPDIR/repo"
mkdir "$FIXTURE"
git -C "$FIXTURE" init -q
git -C "$FIXTURE" config user.email "test@example.com"
git -C "$FIXTURE" config user.name "Test User"

echo "base" > "$FIXTURE/file.txt"
git -C "$FIXTURE" add file.txt
git -C "$FIXTURE" commit -q -m "feat: initial release"
git -C "$FIXTURE" tag v1.0.0

echo "login" >> "$FIXTURE/file.txt"
git -C "$FIXTURE" commit -am "feat(auth): add login flow" -q

echo "bug" >> "$FIXTURE/file.txt"
git -C "$FIXTURE" commit -am "fix: repair session timeout" -q

echo "shape" >> "$FIXTURE/file.txt"
git -C "$FIXTURE" commit -am "refactor: reshape command parser" -q

echo "legacy" >> "$FIXTURE/file.txt"
git -C "$FIXTURE" commit -am "remove: drop legacy option" -q

OUTPUT="$TMPDIR/CHANGELOG.md"
bash "$REPO_ROOT/changelog.sh" --repo "$FIXTURE" --output "$OUTPUT" >/dev/null

grep -q "Generated from commits after \`v1.0.0\`" "$OUTPUT"
grep -q "### Added" "$OUTPUT"
grep -q "add login flow" "$OUTPUT"
grep -q "### Fixed" "$OUTPUT"
grep -q "repair session timeout" "$OUTPUT"
grep -q "### Changed" "$OUTPUT"
grep -q "reshape command parser" "$OUTPUT"
grep -q "### Removed" "$OUTPUT"
grep -q "drop legacy option" "$OUTPUT"

if grep -q "initial release" "$OUTPUT"; then
  echo "pre-tag commit leaked into changelog" >&2
  exit 1
fi

echo "test-changelog.sh passed"
