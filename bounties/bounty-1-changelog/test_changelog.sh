#!/usr/bin/env bash
# test_changelog.sh — Test the changelog generator
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHANGELOG_SCRIPT="$SCRIPT_DIR/changelog.sh"

# Create temp test repo
TEST_DIR=$(mktemp -d)
cd "$TEST_DIR"
git init
git config user.email "test@test.com"
git config user.name "Test"

echo "=== Test 1: No tags, conventional commits ==="

# Create commits with conventional prefixes
echo "feat: add user authentication" > auth.txt && git add auth.txt && git commit -m "feat: add user authentication"
echo "fix: resolve login bug" > fix.txt && git add fix.txt && git commit -m "fix: resolve login bug"
echo "chore: update dependencies" > deps.txt && git add deps.txt && git commit -m "chore: update dependencies"
echo "docs: update README" > readme.txt && git add readme.txt && git commit -m "docs: update README"
echo "refactor: clean up database queries" > db.txt && git add db.txt && git commit -m "refactor: clean up database queries"
echo "remove: delete deprecated endpoint" > remove.txt && git add remove.txt && git commit -m "remove: delete deprecated endpoint"
echo "random commit without prefix" > other.txt && git add other.txt && git commit -m "random commit without prefix"

# Generate changelog
bash "$CHANGELOG_SCRIPT" CHANGELOG.md

echo "--- Generated CHANGELOG.md ---"
cat CHANGELOG.md
echo "---"

# Validate categories
if grep -q "### Added" CHANGELOG.md && \
   grep -q "add user authentication" CHANGELOG.md && \
   grep -q "### Fixed" CHANGELOG.md && \
   grep -q "resolve login bug" CHANGELOG.md && \
   grep -q "### Changed" CHANGELOG.md && \
   grep -q "update dependencies" CHANGELOG.md && \
   grep -q "### Removed" CHANGELOG.md && \
   grep -q "delete deprecated endpoint" CHANGELOG.md && \
   grep -q "### Other" CHANGELOG.md && \
   grep -q "random commit" CHANGELOG.md; then
    echo "✅ Test 1 PASSED: All categories detected correctly"
else
    echo "❌ Test 1 FAILED: Missing expected categories"
    exit 1
fi

echo ""
echo "=== Test 2: With git tags ==="

# Create a tag and more commits
git tag v1.0.0
echo "feat: add new feature" > new.txt && git add new.txt && git commit -m "feat: add new feature"
echo "fix: fix another bug" > fix2.txt && git add fix2.txt && git commit -m "fix: fix another bug"

bash "$CHANGELOG_SCRIPT" CHANGELOG-v2.md

echo "--- Generated CHANGELOG-v2.md ---"
cat CHANGELOG-v2.md
echo "---"

# Should only include commits after v1.0.0
if grep -q "add new feature" CHANGELOG-v2.md && \
   grep -q "fix another bug" CHANGELOG-v2.md && \
   ! grep -q "add user authentication" CHANGELOG-v2.md; then
    echo "✅ Test 2 PASSED: Only commits after tag included"
else
    echo "❌ Test 2 FAILED: Tag filtering not working"
    exit 1
fi

echo ""
echo "=== Test 3: Custom output file ==="
bash "$CHANGELOG_SCRIPT" custom-output.md
if [ -f custom-output.md ]; then
    echo "✅ Test 3 PASSED: Custom output file created"
else
    echo "❌ Test 3 FAILED: Custom output file not created"
    exit 1
fi

# Cleanup
rm -rf "$TEST_DIR"

echo ""
echo "🎉 All tests passed!"
