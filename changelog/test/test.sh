#!/usr/bin/env bash
# Test suite for changelog.sh

set -uo pipefail

SCRIPT="$(dirname "$0")/../changelog.sh"
PASS="\033[32m✓\033[0m"
FAIL="\033[31m✗\033[0m"
PASSED=0
FAILED=0

# Setup temp git repo
TMPDIR=$(mktemp -d)
cd "$TMPDIR"
git init -q
git config user.name "Test"
git config user.email "test@test.com"

# Create commits with various prefixes
echo "init" > file.txt && git add . && git commit -q -m "feat: initial project setup"
echo "b" >> file.txt && git commit -q -am "fix: resolve login crash on empty password"
echo "c" >> file.txt && git commit -q -am "feat(auth): add OAuth2 Google provider"
echo "d" >> file.txt && git commit -q -am "remove: drop legacy API v1 endpoints"
echo "e" >> file.txt && git commit -q -am "docs: update README with API examples"

# Tag an early commit and add more after
git tag v1.0.0

echo "f" >> file.txt && git commit -q -am "fix(ui): button alignment on mobile"
echo "g" >> file.txt && git commit -q -am "chore: update dependencies"
echo "h" >> file.txt && git commit -q -am "refactor: extract validation into shared module"
echo "i" >> file.txt && git commit -q -am "feat: add export to CSV feature"
echo "j" >> file.txt && git commit -q -am "delete: remove deprecated user.legacy field"

echo ""
echo "📋 CHANGELOG Generator — Test Suite"
echo ""

# Test 1: Dry run produces output
OUTPUT=$(bash "$SCRIPT" --dry-run 2>/dev/null)
if echo "$OUTPUT" | grep -q "# Changelog"; then
  echo -e "  $PASS Generates changelog header"
  ((PASSED++)) || true
else
  echo -e "  $FAIL Should generate changelog header"
  ((FAILED++)) || true
fi

# Test 2: Has Added section
if echo "$OUTPUT" | grep -q "### Added"; then
  echo -e "  $PASS Has 'Added' section"
  ((PASSED++)) || true
else
  echo -e "  $FAIL Should have 'Added' section"
  ((FAILED++)) || true
fi

# Test 3: Has Fixed section
if echo "$OUTPUT" | grep -q "### Fixed"; then
  echo -e "  $PASS Has 'Fixed' section"
  ((PASSED++)) || true
else
  echo -e "  $FAIL Should have 'Fixed' section"
  ((FAILED++)) || true
fi

# Test 4: Has Changed section
if echo "$OUTPUT" | grep -q "### Changed"; then
  echo -e "  $PASS Has 'Changed' section"
  ((PASSED++)) || true
else
  echo -e "  $FAIL Should have 'Changed' section"
  ((FAILED++)) || true
fi

# Test 5: Has Removed section
if echo "$OUTPUT" | grep -q "### Removed"; then
  echo -e "  $PASS Has 'Removed' section"
  ((PASSED++)) || true
else
  echo -e "  $FAIL Should have 'Removed' section"
  ((FAILED++)) || true
fi

# Test 6: feat commits go to Added
if echo "$OUTPUT" | grep -q "add export to CSV"; then
  echo -e "  $PASS feat commits categorized as Added"
  ((PASSED++)) || true
else
  echo -e "  $FAIL feat commits should be in Added"
  ((FAILED++)) || true
fi

# Test 7: fix commits go to Fixed
if echo "$OUTPUT" | grep -q "button alignment"; then
  echo -e "  $PASS fix commits categorized as Fixed"
  ((PASSED++)) || true
else
  echo -e "  $FAIL fix commits should be in Fixed"
  ((FAILED++)) || true
fi

# Test 8: remove/delete commits go to Removed
if echo "$OUTPUT" | grep -q "deprecated user.legacy"; then
  echo -e "  $PASS delete commits categorized as Removed"
  ((PASSED++)) || true
else
  echo -e "  $FAIL delete commits should be in Removed"
  ((FAILED++)) || true
fi

# Test 9: chore/docs/refactor go to Changed
if echo "$OUTPUT" | grep -q "update dependencies"; then
  echo -e "  $PASS chore commits categorized as Changed"
  ((PASSED++)) || true
else
  echo -e "  $FAIL chore commits should be in Changed"
  ((FAILED++)) || true
fi

# Test 10: --since tag works
SINCE_OUTPUT=$(bash "$SCRIPT" --dry-run --since v1.0.0 2>/dev/null)
SINCE_LINES=$(echo "$SINCE_OUTPUT" | grep -c "^-" || true)
if [ "$SINCE_LINES" -eq 5 ]; then
  echo -e "  $PASS --since tag filters correctly (5 commits since v1.0.0)"
  ((PASSED++)) || true
else
  echo -e "  $FAIL --since should show 5 commits, got $SINCE_LINES"
  ((FAILED++)) || true
fi

# Test 11: --version flag
VERSIONED=$(bash "$SCRIPT" --dry-run --version "2.0.0" 2>/dev/null)
if echo "$VERSIONED" | grep -q "\[2.0.0\]"; then
  echo -e "  $PASS --version flag sets version label"
  ((PASSED++)) || true
else
  echo -e "  $FAIL --version should set custom label"
  ((FAILED++)) || true
fi

# Test 12: File output (non-dry-run)
bash "$SCRIPT" --output "$TMPDIR/CHANGELOG.md" 2>/dev/null
if [ -f "$TMPDIR/CHANGELOG.md" ]; then
  echo -e "  $PASS Writes CHANGELOG.md file"
  ((PASSED++)) || true
else
  echo -e "  $FAIL Should write CHANGELOG.md"
  ((FAILED++)) || true
fi

# Test 13: Commit hashes included
if echo "$OUTPUT" | grep -qP '\(`[a-f0-9]+`\)'; then
  echo -e "  $PASS Includes commit hashes"
  ((PASSED++)) || true
else
  echo -e "  $FAIL Should include commit hashes"
  ((FAILED++)) || true
fi

echo ""
echo "────────────────────────────────────────"
echo "Results: $PASSED passed, $FAILED failed"

# Cleanup
rm -rf "$TMPDIR"
exit $FAILED
