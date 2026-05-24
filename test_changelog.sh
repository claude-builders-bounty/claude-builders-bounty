#!/usr/bin/env bash
set -e

# Setup test repo
rm -rf test_repo
mkdir test_repo
cd test_repo
git init

git commit --allow-empty -m "Initial commit"
git tag v1.0.0

git commit --allow-empty -m "feat: Add new auth module"
git commit --allow-empty -m "fix(ui): Resolve button padding issue"
git commit --allow-empty -m "refactor: Cleanup old code"
git commit --allow-empty -m "remove: Drop deprecated API"
git commit --allow-empty -m "chore: Update dependencies"
git commit --allow-empty -m "Something without a conventional prefix"

cp ../skills/changelog-generator/changelog.sh .
chmod +x changelog.sh
./changelog.sh

echo "--- CHANGELOG.md ---"
cat CHANGELOG.md
echo "--------------------"

cd ..
rm -rf test_repo
