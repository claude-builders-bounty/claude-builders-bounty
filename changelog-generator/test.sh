#!/usr/bin/env bash
# test.sh — Test changelog.sh on a real git repo with sample commits
set -euo pipefail

SELF="${BASH_SOURCE[0]:-$0}"
SCRIPT_DIR="$(cd "$(dirname "$SELF")" && pwd)"

TEST_DIR=$(mktemp -d)
echo "🧪 Creating test repo at: $TEST_DIR"

cp "$SCRIPT_DIR/changelog.sh" "$TEST_DIR/changelog.sh"
chmod +x "$TEST_DIR/changelog.sh"

cd "$TEST_DIR"
git init
git config user.email "test@example.com"
git config user.name "Test User"

echo "v1.0.0" > version.txt
git add version.txt
git commit -m "feat: initial release"
git tag v1.0.0

echo "new-feature" > feature.txt && git add feature.txt && git commit -m "feat: add user authentication module"
echo "another" > another.txt && git add another.txt && git commit -m "add dashboard widgets"
echo "fix" > fix.txt && git add fix.txt && git commit -m "fix: resolve login timeout issue"
echo "fix2" > fix2.txt && git add fix2.txt && git commit -m "bug: correct timezone offset in scheduler"
echo "change" > change.txt && git add change.txt && git commit -m "refactor: simplify database connection pool"
echo "change2" > change2.txt && git add change2.txt && git commit -m "update: upgrade dependencies to latest versions"
echo "remove" > remove.txt && git add remove.txt && git commit -m "remove: delete deprecated API endpoints"
echo "remove2" > remove2.txt && git add remove2.txt && git commit -m "deprecate: mark legacy sync method as deprecated"
echo "other" > other.txt && git add other.txt && git commit -m "chore: update CI configuration"

bash ./changelog.sh . --output "$TEST_DIR/CHANGELOG.md"

echo ""
echo "📋 Generated CHANGELOG.md:"
echo "=========================="
cat "$TEST_DIR/CHANGELOG.md"
echo "=========================="

echo ""
PASSED=0
FAILED=0

check() {
    if grep -q "$1" "$TEST_DIR/CHANGELOG.md"; then
        echo "  ✅ $2"; PASSED=$((PASSED + 1))
    else
        echo "  ❌ $2"; FAILED=$((FAILED + 1))
    fi
}

check "### Added" "Added section present"
check "### Fixed" "Fixed section present"
check "### Changed" "Changed section present"
check "### Removed" "Removed section present"
check "user authentication module" "Commit content correct"
check "resolve login timeout issue" "Fixed content correct"
check "simplify database connection pool" "Changed content correct"
check "delete deprecated API endpoints" "Removed content correct"

echo ""
echo "Results: $PASSED passed, $FAILED failed"
rm -rf "$TEST_DIR"

if [[ $FAILED -eq 0 ]]; then
    echo "🎉 All tests passed!"
    exit 0
else
    echo "💥 Some tests failed!"
    exit 1
fi
