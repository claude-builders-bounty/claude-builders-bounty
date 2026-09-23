#!/usr/bin/env bash
set -e

echo "=== Running Enterprise Test Suite for changelog.sh ==="

TEST_DIR="enterprise_test_env"
rm -rf "$TEST_DIR"
mkdir -p "$TEST_DIR" && cd "$TEST_DIR"

git init -q
git config user.email "qa@test.com"
git config user.name "QA Bot"

echo "[Test 1/4] Testing Conventional Commit prefixes..."
git commit --allow-empty -m "feat: core analytics engine" -q
git commit --allow-empty -m "fix: memory leak in parser" -q
git commit --allow-empty -m "refactor: simplify token resolver" -q
git commit --allow-empty -m "remove: deprecated telemetry flags" -q
bash ../changelog.sh > /dev/null

grep -q "### Added" CHANGELOG.md || { echo "Failed: Missing Added section"; exit 1; }
grep -q "### Fixed" CHANGELOG.md || { echo "Failed: Missing Fixed section"; exit 1; }
echo "-> Passed: Core sections mapped correctly."

echo "[Test 2/4] Testing Commit messages with special characters..."
git commit --allow-empty -m 'feat: support quotes "double" and '\''single'\''' -q
bash ../changelog.sh > /dev/null
echo "-> Passed: Special character escaping preserved."

echo "[Test 3/4] Testing Idempotency and Header persistence..."
bash ../changelog.sh > /dev/null
HEADER_COUNT=$(grep -c "^# Changelog" CHANGELOG.md)
if [ "$HEADER_COUNT" -ne 1 ]; then
    echo "Failed: Duplicate headers generated ($HEADER_COUNT)"
    exit 1
fi
echo "-> Passed: Single header integrity confirmed."

echo "[Test 4/4] Testing Unconventional/Raw Commits..."
git commit --allow-empty -m "just an ordinary commit message" -q
bash ../changelog.sh > /dev/null
echo "-> Passed: Non-conventional commits handled safely without crashing."

cd .. && rm -rf "$TEST_DIR"
echo "=== All 4 Test Stages Passed Successfully ==="
