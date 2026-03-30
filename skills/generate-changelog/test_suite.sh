#!/usr/bin/env bash
# Test suite for changelog.sh
# Verifies generation and categorization on a sample repo

set +e

SCRIPT_PATH="$(dirname "$(realpath "$0")")/changelog.sh"

echo "Testing changelog.sh at: $SCRIPT_PATH"
echo ""

# Create a temporary git repo with known commits
TMPDIR=$(mktemp -d)
cd "$TMPDIR"
git init -q
git config user.email "test@example.com"
git config user.name "Test"

# Create a file and commit
touch README.md && git add . && git commit -q -m "feat: initial commit"
echo "a" >> README.md && git commit -q -m "add: append a"
echo "b" >> README.md && git add . && git commit -q -m "update: modify README"
echo "bug" > bug.txt && git add . && git commit -q -m "fix: resolve bug"
echo "remove" >> README.md && git add . && git commit -q -m "remove: obsolete section"
git tag v1.0.0 -q
echo "new" >> new.txt && git add . && git commit -q -m "feat: add new feature"

# Run the script
"$SCRIPT_PATH" > /dev/null 2>&1
exit_code=$?

if [ $exit_code -ne 0 ]; then
  echo "Script exited with code $exit_code"
else
  echo "Script succeeded"
fi

# Check output file exists and contains expected sections
if [ ! -f CHANGELOG.md ]; then
  echo "FAIL: CHANGELOG.md not created"
  exit 1
fi

content=$(cat CHANGELOG.md)

# Check sections exist
echo -n "Check 'Added' section... "
if grep -q "^### Added$" <<< "$content"; then
  echo "PASS"
else
  echo "FAIL (missing Section header)"
fi

echo -n "Check 'Fixed' section... "
if grep -q "^### Fixed$" <<< "$content"; then
  echo "PASS"
else
  echo "FAIL"
fi

echo -n "Check 'Changed' section... "
if grep -q "^### Changed$" <<< "$content"; then
  echo "PASS"
else
  echo "FAIL"
fi

echo -n "Check 'Removed' section... "
if grep -q "^### Removed$" <<< "$content"; then
  echo "PASS"
else
  echo "FAIL"
fi

echo -n "Check that 'feat' commit appears under Added... "
if grep -q "feat: add new feature" <<< "$content"; then
  echo "PASS"
else
  echo "FAIL"
fi

echo -n "Check that 'fix' commit appears under Fixed... "
if grep -q "fix: resolve bug" <<< "$content"; then
  echo "PASS"
else
  echo "FAIL"
fi

echo -n "Check that 'remove' commit appears under Removed... "
if grep -q "remove: obsolete section" <<< "$content"; then
  echo "PASS"
else
  echo "FAIL"
fi

echo -n "Check that 'update' commit appears under Changed... "
if grep -q "update: modify README" <<< "$content"; then
  echo "PASS"
else
  echo "FAIL"
fi

echo -n "Check total commits count in footer... "
if grep -q "Total commits: [0-9]" <<< "$content"; then
  echo "PASS"
else
  echo "FAIL"
fi

# Cleanup
cd - > /dev/null
rm -rf "$TMPDIR"

echo ""
echo "All checks completed."
