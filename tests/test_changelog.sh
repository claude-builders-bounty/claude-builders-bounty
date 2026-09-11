#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT="$SCRIPT_DIR/changelog.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fail() {
    printf 'FAIL: %s\n' "$1" >&2
    exit 1
}

assert_contains() {
    grep -Fq -- "$2" "$1" || fail "Expected '$2' in $1"
}

new_repo() {
    local dir="$1"

    mkdir -p "$dir"
    cd "$dir"

    git init -q
    git config user.email "test@example.com"
    git config user.name "Test User"

    printf 'initial\n' > file.txt
    git add file.txt
    git commit -qm "initial commit"
}

# Test 1: categorization after a tag.
new_repo "$TMP/tagged"

git tag v1.0.0

printf 'feature\n' >> file.txt
git add file.txt
git commit -qm "feat: add streaming support"

printf 'bugfix\n' >> file.txt
git add file.txt
git commit -qm "fix: handle empty responses"

printf 'docs\n' >> file.txt
git add file.txt
git commit -qm "docs: improve installation guide"

printf 'removed\n' >> file.txt
git add file.txt
git commit -qm "remove: deprecated API"

OUTPUT="$TMP/tagged/CHANGELOG.md"
"$SCRIPT" "$OUTPUT" >/dev/null

assert_contains "$OUTPUT" "## Added"
assert_contains "$OUTPUT" "add streaming support"
assert_contains "$OUTPUT" "## Changed"
assert_contains "$OUTPUT" "improve installation guide"
assert_contains "$OUTPUT" "## Fixed"
assert_contains "$OUTPUT" "handle empty responses"
assert_contains "$OUTPUT" "## Removed"
assert_contains "$OUTPUT" "deprecated API"

# Test 2: repository without tags.
new_repo "$TMP/untagged"

printf 'feature\n' >> file.txt
git add file.txt
git commit -qm "feat: add initial feature"

OUTPUT="$TMP/untagged/CHANGELOG.md"
"$SCRIPT" "$OUTPUT" >/dev/null

assert_contains "$OUTPUT" "add initial feature"

# Test 3: custom output path.
CUSTOM="$TMP/custom.md"
cd "$TMP/tagged"
"$SCRIPT" "$CUSTOM" >/dev/null

[[ -f "$CUSTOM" ]] || fail "Custom output file was not created"
assert_contains "$CUSTOM" "# Changelog"

printf 'PASS: all changelog tests\n'
