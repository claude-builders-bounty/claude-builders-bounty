#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$ROOT_DIR/generate-changelog/changelog.sh"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

cd "$TMP_DIR"
git init -q
git config user.name "Test User"
git config user.email "test@example.com"

touch app.txt
git add app.txt
git commit -q -m "chore: initial release"
git tag v1.0.0

echo "feature" >> app.txt
git add app.txt
git commit -q -m "feat: add OAuth login"

echo "fix" >> app.txt
git add app.txt
git commit -q -m "fix: prevent duplicate webhooks"

echo "docs" >> app.txt
git add app.txt
git commit -q -m "docs: update deployment notes"

echo "remove" >> app.txt
git add app.txt
git commit -q -m "remove deprecated invite endpoint"

bash "$SCRIPT" >/tmp/generate-changelog-test.log

test -f CHANGELOG.md
grep -q "Changes since tag.*v1.0.0" CHANGELOG.md
grep -q "## Added" CHANGELOG.md
grep -q "feat: add OAuth login" CHANGELOG.md
grep -q "## Fixed" CHANGELOG.md
grep -q "fix: prevent duplicate webhooks" CHANGELOG.md
grep -q "## Changed" CHANGELOG.md
grep -q "docs: update deployment notes" CHANGELOG.md
grep -q "## Removed" CHANGELOG.md
grep -q "remove deprecated invite endpoint" CHANGELOG.md

echo "generate-changelog tests passed"
