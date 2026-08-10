#!/usr/bin/env bash
#
# test_changelog.sh — Automated acceptance tests for changelog.sh
#
# Usage: bash test_changelog.sh
#
# Verifies every acceptance criterion of the bounty:
#   1. Works via `bash changelog.sh`
#   2. Fetches commits since the last git tag
#   3. Auto-categorizes into Added / Fixed / Changed / Removed
#   4. Outputs a properly formatted CHANGELOG.md
#   5. Handles edge cases (no tags, scopes, breaking changes, uppercase)
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHANGELOG_SH="$SCRIPT_DIR/../changelog.sh"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

PASS=0
FAIL=0

ok()   { PASS=$((PASS + 1)); echo "  PASS: $1"; }
fail() { FAIL=$((FAIL + 1)); echo "  FAIL: $1"; }

assert_contains() { # file, needle, label
  if grep -qF -- "$2" "$1"; then ok "$3"; else fail "$3 (missing: $2)"; fi
}

assert_not_contains() { # file, needle, label
  if grep -qF -- "$2" "$1"; then fail "$3 (unexpected: $2)"; else ok "$3"; fi
}

echo "==> Setting up test repository"
git init -q "$WORK/repo"
cd "$WORK/repo"
git config user.email "test@example.com"
git config user.name "Test Runner"

commit() { # message
  echo "$1" >> history.txt
  git add history.txt
  git commit -q -m "$1"
}

# --- Pre-tag commits (must NOT appear in the changelog) ---------------------
commit "feat: initial scaffold"
commit "fix: bootstrap bug"
git tag v1.0.0

# --- Post-tag commits (must appear, one per category) -----------------------
commit "feat: add search input"
commit "feat(api): introduce pagination"
commit "feat!: redesign auth flow"
commit "FIX: crash on empty state"
commit "fix(ui): button alignment"
commit "refactor: extract auth service"
commit "chore: bump dependencies"
commit "docs: update README"
commit "remove: legacy endpoint"
commit "delete: old config file"
commit "plain message without prefix"

echo "==> Test 1: default run (since last tag)"
bash "$CHANGELOG_SH" >/dev/null
assert_contains CHANGELOG.md "## [Unreleased] (since v1.0.0)" "section title includes last tag"
assert_contains CHANGELOG.md "### Added" "Added section present"
assert_contains CHANGELOG.md "### Fixed" "Fixed section present"
assert_contains CHANGELOG.md "### Changed" "Changed section present"
assert_contains CHANGELOG.md "### Removed" "Removed section present"
assert_contains CHANGELOG.md "- add search input" "feat: -> Added"
assert_contains CHANGELOG.md "- introduce pagination" "feat(scope): -> Added"
assert_contains CHANGELOG.md "- redesign auth flow" "feat!: -> Added (breaking change)"
assert_contains CHANGELOG.md "- crash on empty state" "FIX: -> Fixed (case-insensitive)"
assert_contains CHANGELOG.md "- button alignment" "fix(scope): -> Fixed"
assert_contains CHANGELOG.md "- extract auth service" "refactor: -> Changed"
assert_contains CHANGELOG.md "- bump dependencies" "chore: -> Changed"
assert_contains CHANGELOG.md "- update README" "docs: -> Changed"
assert_contains CHANGELOG.md "- legacy endpoint" "remove: -> Removed"
assert_contains CHANGELOG.md "- old config file" "delete: -> Removed"
assert_contains CHANGELOG.md "- plain message without prefix" "no prefix -> Changed (default)"
assert_not_contains CHANGELOG.md "initial scaffold" "pre-tag commit excluded"
assert_not_contains CHANGELOG.md "bootstrap bug" "pre-tag commit excluded"

echo "==> Test 2: custom output path"
bash "$CHANGELOG_SH" --output custom.md >/dev/null
assert_contains custom.md "# Changelog" "--output writes to custom path"

echo "==> Test 3: --since flag"
bash "$CHANGELOG_SH" --since v1.0.0 --output since.md >/dev/null
assert_contains since.md "(since v1.0.0)" "--since uses given tag"

echo "==> Test 4: no tags -> full history"
git tag -d v1.0.0 >/dev/null
bash "$CHANGELOG_SH" --output notag.md >/dev/null
assert_contains notag.md "## [Unreleased]" "no-tag fallback title"
assert_contains notag.md "initial scaffold" "no-tag includes full history"
git tag v1.0.0

echo "==> Test 5: --all ignores tags"
bash "$CHANGELOG_SH" --all --output all.md >/dev/null
assert_contains all.md "initial scaffold" "--all includes full history"

echo "==> Test 6: not a git repo -> clean error"
mkdir -p "$WORK/notrepo"
cd "$WORK/notrepo"
if bash "$CHANGELOG_SH" 2>/dev/null; then
  fail "non-repo run should exit non-zero"
else
  ok "non-repo run exits non-zero"
fi

echo ""
echo "=========================================="
echo "  Results: $PASS passed, $FAIL failed"
echo "=========================================="
[[ "$FAIL" -eq 0 ]] || exit 1