#!/usr/bin/env bash
set -euo pipefail

# Test script for changelog.sh
# Runs on a fake git repo to validate output

TEST_DIR=$(mktemp -d)
trap "rm -rf $TEST_DIR" EXIT

cd "$TEST_DIR"
git init -b main
git config user.email "test@test.com"
git config user.name "Tester"

# Create some test commits
echo "# Project" > README.md
git add README.md
git commit -m "Initial commit" --no-gpg-sign

git tag v0.1.0

echo "console.log('hello')" > index.js
git add index.js
git commit -m "feat: add console greeting" --no-gpg-sign

echo "console.log('world')" >> index.js
git add index.js
git commit -m "fix: correct greeting punctuation" --no-gpg-sign

echo "// config" > config.js
git add config.js
git commit -m "add configuration file" --no-gpg-sign

echo "" > README.md
git add README.md
git commit -m "docs: update README with usage" --no-gpg-sign

rm -f config.js
git add -A
git commit -m "remove: drop config.js, no longer needed" --no-gpg-sign

# Add a refactor
echo "// refactored" > index.js
git add index.js
git commit -m "refactor: simplify greeting logic" --no-gpg-sign

# Run the script
bash /tmp/changelog-bounty/changelog.sh --output "$TEST_DIR/CHANGELOG.md"

echo ""
echo "=== Generated CHANGELOG.md ==="
cat "$TEST_DIR/CHANGELOG.md"

# Validation checks
echo ""
echo "=== Validating Content ==="

# Check categories
if grep -q "### Added" "$TEST_DIR/CHANGELOG.md"; then echo "✅ Added section found"; else echo "❌ Missing Added section"; exit 1; fi
if grep -q "### Fixed" "$TEST_DIR/CHANGELOG.md"; then echo "✅ Fixed section found"; else echo "❌ Missing Fixed section"; exit 1; fi
if grep -q "### Changed" "$TEST_DIR/CHANGELOG.md"; then echo "✅ Changed section found"; else echo "❌ Missing Changed section"; exit 1; fi
if grep -q "### Removed" "$TEST_DIR/CHANGELOG.md"; then echo "✅ Removed section found"; else echo "❌ Missing Removed section"; exit 1; fi

# Check content
if grep -q "console greeting\|greeting" "$TEST_DIR/CHANGELOG.md"; then echo "✅ 'greeting' commit found"; else echo "❌ Missing 'greeting' commit"; exit 1; fi
if grep -q "punctuation\|correct" "$TEST_DIR/CHANGELOG.md"; then echo "✅ 'punctuation' commit found"; else echo "❌ Missing 'punctuation' commit"; exit 1; fi

# Check it's a valid markdown file
if head -1 "$TEST_DIR/CHANGELOG.md" | grep -q "^# "; then echo "✅ Valid CHANGELOG.md format"; else echo "❌ Invalid format"; exit 1; fi

echo ""
echo "🎉 All tests passed!"