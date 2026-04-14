#!/usr/bin/env bash
# Test the changelog generator
set -euo pipefail

# Create a temporary git repo
TMPDIR=$(mktemp -d)
cd "$TMPDIR"
git init
git config user.email "test@test.com"
git config user.name "Test"

# Create some commits
echo "v1" > file.txt
git add file.txt
git commit -m "feat: add initial file"
git tag v1.0.0

echo "v2" > file.txt
git commit -am "fix: update file content"

echo "v3" > file.txt
git commit -am "refactor: improve file structure"

# Run changelog generator
cp /home/ubuntu/kova/claude-builders-bounty/changelog/generate-changelog.sh .
bash generate-changelog.sh --output test_changelog.md

# Check output
if [ -f test_changelog.md ]; then
    echo "✅ Changelog generated successfully!"
    echo "---"
    cat test_changelog.md
else
    echo "❌ Changelog generation failed!"
    exit 1
fi

# Cleanup
cd /
rm -rf "$TMPDIR"
