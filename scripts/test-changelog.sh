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
commit "fix: post-tag regression"
commit "security: patch jwt validation"
commit "chore!: drop legacy api"
commit "feat!: remove deprecated export"

bash "$ROOT/scripts/changelog.sh" "$TMP"

grep -q "### Added" "$TMP/CHANGELOG.md"
bash "$ROOT/scripts/changelog.sh" -o "$TMP/RELEASE.md" "$TMP"
grep -q "### Added" "$TMP/RELEASE.md"
grep -q "### Fixed" "$TMP/CHANGELOG.md"
grep -q "### Security" "$TMP/CHANGELOG.md"
grep -q "### Changed" "$TMP/CHANGELOG.md"
grep -q "export csv" "$TMP/CHANGELOG.md"
grep -q "patch jwt" "$TMP/CHANGELOG.md"
grep -q "drop legacy api" "$TMP/CHANGELOG.md"
grep -q "remove deprecated export" "$TMP/CHANGELOG.md"
if grep -q "add login" "$TMP/CHANGELOG.md"; then
  echo "pre-tag commit 'add login' must not appear in changelog" >&2
  exit 1
fi

echo "changelog tests passed"
