#!/usr/bin/env bash
echo "Running tests..."
mkdir -p test_env && cd test_env
git init -q
git config user.email "test@test.com"; git config user.name "Test"
git commit --allow-empty -m "feat: first feature" -q
git commit --allow-empty -m "fix: first bug" -q
bash ../changelog.sh > /dev/null
if grep -q "### Added" CHANGELOG.md && grep -q "### Fixed" CHANGELOG.md; then
    echo "Test Passed!"
else
    echo "Test Failed!" && exit 1
fi
cd .. && rm -rf test_env
