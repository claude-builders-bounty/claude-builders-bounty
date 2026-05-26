#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

git -C "$TMP" init -q
git -C "$TMP" config user.email "test@example.com"
git -C "$TMP" config user.name "Test"

commit() {
  local msg="$1"
  echo x >>"$TMP/readme.md"
  git -C "$TMP" add readme.md
  git -C "$TMP" commit -q -m "$msg"
}

commit "feat: add login"
commit "fix: handle null token"
commit "chore: bump deps"
git -C "$TMP" tag v1.0.0 -m "v1"
commit "feat: export csv"
commit "security: patch jwt validation"

bash "$ROOT/scripts/changelog.sh" "$TMP"

grep -q "### Added" "$TMP/CHANGELOG.md"
grep -q "### Fixed" "$TMP/CHANGELOG.md"
grep -q "### Security" "$TMP/CHANGELOG.md"
grep -q "export csv" "$TMP/CHANGELOG.md"
grep -q "patch jwt" "$TMP/CHANGELOG.md"
! grep -q "add login" "$TMP/CHANGELOG.md" || true

echo "changelog tests passed"
