#!/usr/bin/env bash
# ==============================================================================
# Automated Test Suite for changelog.sh
# Tests git log parsing, tag range resolution, and markdown categorization.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHANGELOG_SCRIPT="${SCRIPT_DIR}/../changelog.sh"

TEST_REPO="$(mktemp -d)"
trap 'rm -rf "$TEST_REPO"' EXIT

echo "==> Setting up mock git repo at: ${TEST_REPO}"
cd "$TEST_REPO"
git init -q
git config user.name "Test Bot"
git config user.email "bot@test.local"

# Initial commit & tag
echo "initial" > init.txt
git add init.txt
git commit -qm "chore: initial commit"
git tag v1.0.0

# Add commits representing each category
echo "feat1" > f1.txt && git add f1.txt && git commit -qm "feat: add user authentication via OAuth2"
echo "fix1" > f2.txt && git add f2.txt && git commit -qm "fix: prevent token expiration race condition"
echo "refactor1" > f3.txt && git add f3.txt && git commit -qm "refactor: optimize database query latency"
echo "rm1" > f4.txt && git add f4.txt && git commit -qm "remove: drop deprecated legacy XML parser"
echo "sec1" > f5.txt && git add f5.txt && git commit -qm "security: patch input sanitization CVE-2026-001"

echo "==> Running changelog.sh..."
bash "$CHANGELOG_SCRIPT" "TEST_CHANGELOG.md" "v1.0.0" "v1.1.0"

echo "==> Verifying generated changelog..."
if [ ! -f "TEST_CHANGELOG.md" ]; then
    echo "FAIL: TEST_CHANGELOG.md was not created." >&2
    exit 1
fi

CONTENT="$(cat TEST_CHANGELOG.md)"

assert_contains() {
    local needle="$1"
    if ! echo "$CONTENT" | grep -Fq "$needle"; then
        echo "FAIL: Expected to find '${needle}' in changelog output." >&2
        echo "--- Changelog Content ---"
        echo "$CONTENT"
        exit 1
    fi
}

assert_contains "## [v1.1.0]"
assert_contains "### Added"
assert_contains "add user authentication via OAuth2"
assert_contains "### Fixed"
assert_contains "prevent token expiration race condition"
assert_contains "### Changed"
assert_contains "optimize database query latency"
assert_contains "### Removed"
assert_contains "drop deprecated legacy XML parser"
assert_contains "### Security"
assert_contains "patch input sanitization CVE-2026-001"

echo "PASS: All changelog categories and commit messages verified successfully!"
