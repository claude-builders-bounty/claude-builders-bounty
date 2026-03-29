#!/bin/bash
set -e

echo "Running tests for changelog.sh..."

# Create a temporary directory for the test git repository
TEST_DIR=$(mktemp -d)
SCRIPT_DIR=$(pwd)
CHANGELOG_SCRIPT="${SCRIPT_DIR}/changelog.sh"

cd "$TEST_DIR"
git init > /dev/null 2>&1
git config user.email "test@example.com"
git config user.name "Test User"

# Create some commits
touch a && git add a && git commit -m "feat: add new user login" > /dev/null 2>&1
touch b && git add b && git commit -m "fix: resolve crash on startup" > /dev/null 2>&1
touch c && git add c && git commit -m "drop: old unused API" > /dev/null 2>&1
touch d && git add d && git commit -m "refactor: clean up database connections" > /dev/null 2>&1

# Run the script
bash "$CHANGELOG_SCRIPT" > /dev/null

# Verify the output
if [ ! -f "CHANGELOG.md" ]; then
    echo "FAIL: CHANGELOG.md was not created"
    exit 1
fi

if ! grep -q "### Added" CHANGELOG.md; then
    echo "FAIL: Missing 'Added' category"
    exit 1
fi

if ! grep -q "### Fixed" CHANGELOG.md; then
    echo "FAIL: Missing 'Fixed' category"
    exit 1
fi

if ! grep -q "### Removed" CHANGELOG.md; then
    echo "FAIL: Missing 'Removed' category"
    exit 1
fi

if ! grep -q "### Changed" CHANGELOG.md; then
    echo "FAIL: Missing 'Changed' category"
    exit 1
fi

echo "All tests passed successfully!"
cd "$SCRIPT_DIR"
rm -rf "$TEST_DIR"
