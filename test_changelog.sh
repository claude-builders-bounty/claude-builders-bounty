#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

git init -q "$WORKDIR/repo"
git -C "$WORKDIR/repo" config user.email "test@example.com"
git -C "$WORKDIR/repo" config user.name "Changelog Test"

commit_file() {
  file="$1"
  message="$2"
  printf '%s\n' "$message" >> "$WORKDIR/repo/$file"
  git -C "$WORKDIR/repo" add "$file"
  git -C "$WORKDIR/repo" commit -q -m "$message"
}

commit_file "app.txt" "chore: initial release"
git -C "$WORKDIR/repo" tag v1.0.0
commit_file "feature.txt" "feat: add export flow"
commit_file "fix.txt" "fix(input): prevent duplicate submit"
commit_file "refactor.txt" "refactor: simplify parser"
commit_file "remove.txt" "remove: legacy config"

OUTPUT="$WORKDIR/repo/CHANGELOG.md"
bash "$SCRIPT_DIR/changelog.sh" "$OUTPUT" "$WORKDIR/repo"

grep -q "Changes since \`v1.0.0\`" "$OUTPUT"
grep -q "### Added" "$OUTPUT"
grep -q -- "- add export flow" "$OUTPUT"
grep -q "### Fixed" "$OUTPUT"
grep -q -- "- prevent duplicate submit" "$OUTPUT"
grep -q "### Changed" "$OUTPUT"
grep -q -- "- simplify parser" "$OUTPUT"
grep -q "### Removed" "$OUTPUT"
grep -q -- "- legacy config" "$OUTPUT"

if grep -q "initial release" "$OUTPUT"; then
  printf 'Expected commits before v1.0.0 to be excluded\n' >&2
  exit 1
fi

printf 'test_changelog.sh: all checks passed\n'
