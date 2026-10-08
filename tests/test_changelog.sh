#!/usr/bin/env bash
set -euo pipefail

echo "=== Running Changelog Generator Test Suite ==="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_REPO=$(mktemp -d)
trap 'rm -rf "$TEST_REPO"' EXIT

cd "$TEST_REPO"
git init -q
git config user.name "Tester"
git config user.email "test@example.com"

# 1. Base commit and initial tag v1.0.0
echo "initial" > file.txt
git add file.txt
git commit -qm "feat: initial feature"
git tag v1.0.0

# 2. Commits for next release
echo "feat1" >> file.txt
git commit -aqm "feat(auth): add OAuth2 token support"

echo "fix1" >> file.txt
git commit -aqm "fix(api): fix null pointer on missing user"

echo "refactor1" >> file.txt
git commit -aqm "refactor(core): optimize memory usage in parser"

echo "remove1" >> file.txt
git commit -aqm "remove(legacy): remove deprecated v1 endpoint"

# 3. Run changelog generator
"$SCRIPT_DIR/changelog.sh" "$TEST_REPO"

# 4. Assertions
CHANGELOG="$TEST_REPO/CHANGELOG.md"

if [ ! -f "$CHANGELOG" ]; then
  echo "❌ Error: CHANGELOG.md was not created!"
  exit 1
fi

grep -q "Unreleased (since v1.0.0)" "$CHANGELOG" || { echo "❌ Failed: Tag range header missing"; exit 1; }
grep -q "### Added" "$CHANGELOG" || { echo "❌ Failed: Added section missing"; exit 1; }
grep -q "add OAuth2 token support" "$CHANGELOG" || { echo "❌ Failed: Added entry missing"; exit 1; }
grep -q "### Fixed" "$CHANGELOG" || { echo "❌ Failed: Fixed section missing"; exit 1; }
grep -q "fix null pointer on missing user" "$CHANGELOG" || { echo "❌ Failed: Fixed entry missing"; exit 1; }
grep -q "### Changed" "$CHANGELOG" || { echo "❌ Failed: Changed section missing"; exit 1; }
grep -q "optimize memory usage in parser" "$CHANGELOG" || { echo "❌ Failed: Changed entry missing"; exit 1; }
grep -q "### Removed" "$CHANGELOG" || { echo "❌ Failed: Removed section missing"; exit 1; }
grep -q "remove deprecated v1 endpoint" "$CHANGELOG" || { echo "❌ Failed: Removed entry missing"; exit 1; }

echo "✅ All changelog tests passed successfully!"
