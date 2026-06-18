#!/usr/bin/env bash
# test_changelog.sh - Manual smoke tests for changelog.sh
# Run: bash tests/test_changelog.sh
#
# Creates a temp git repo with known commit history, runs changelog.sh,
# and verifies the output. Exits 0 on success, non-zero on failure.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CHANGELOG_SH="${REPO_ROOT}/skills/changelog/changelog.sh"

if [ ! -f "$CHANGELOG_SH" ]; then
    echo "FAIL: changelog.sh not found at $CHANGELOG_SH" >&2
    exit 1
fi

TMPDIR="$(mktemp -d)"
trap "rm -rf $TMPDIR" EXIT

cd "$TMPDIR"
git init -q
git config user.email "test@test.com"
git config user.name "Test"

# Helper: create empty commit with given message
commit() { git commit --allow-empty -q -m "$1"; }

# Stage 1: pre-tag commits
commit "feat: initial user module"
commit "docs: add README"

git tag v1.0.0

# Stage 2: post-tag commits covering all 4 categories
commit "feat: dashboard widgets"
commit "feat(api): add /users endpoint"
commit "fix: crash on empty input"
commit "fix(api): handle 404 in /users"
commit "docs: update README with new endpoints"
commit "refactor: extract auth helper"
commit "perf: cache user lookup"
commit "chore: bump deps"
commit "BREAKING: remove v1 API"
commit "revert: undo feature X"
commit "Remove legacy config"

# Run the script
OUTPUT="$TMPDIR/CHANGELOG.md"
bash "$CHANGELOG_SH" "$OUTPUT"

# Validate output
fail=0
expect_line() {
    local pattern="$1"
    if ! grep -qE "$pattern" "$OUTPUT"; then
        echo "FAIL: expected line matching: $pattern" >&2
        fail=1
    fi
}

# Header
expect_line "^# Changelog$"
expect_line "^## \[1\.0\.0 - [0-9-]+\]$"

# Categories
expect_line "^### Added$"
expect_line "^- dashboard widgets$"
expect_line "^- add /users endpoint$"

expect_line "^### Fixed$"
expect_line "^- crash on empty input$"
expect_line "^- handle 404 in /users$"

expect_line "^### Changed$"
expect_line "^- extract auth helper$"
expect_line "^- cache user lookup$"
expect_line "^- bump deps$"

expect_line "^### Removed$"
expect_line "^- remove v1 API$"
expect_line "^- undo feature X$"
expect_line "^- Remove legacy config$"

# Prefixes should NOT appear in output (stripped)
if grep -qE "^- (feat|fix|docs|refactor|perf|chore|BREAKING|revert): " "$OUTPUT"; then
    echo "FAIL: commit prefixes leaked into output" >&2
    fail=1
fi

if [ "$fail" -eq 0 ]; then
    echo "OK: all changelog tests passed"
    cat "$OUTPUT"
    exit 0
else
    echo "FAILED" >&2
    cat "$OUTPUT" >&2
    exit 1
fi
