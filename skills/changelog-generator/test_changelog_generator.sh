#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
TMP_REPO=$(mktemp -d)
trap 'rm -rf "$TMP_REPO"' EXIT

PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); }
fail() { FAIL=$((FAIL + 1)); echo "  FAIL: $1"; }

# --- Setup temp repo (no tag) ---
cd "$TMP_REPO"
git init -q
git config user.email "test@test.com"
git config user.name "Test"

git commit --allow-empty -q -m "init: project setup"
git commit --allow-empty -q -m "feat: add login page"
git commit --allow-empty -q -m "fix: correct off-by-one"
git commit --allow-empty -q -m "chore: update dependencies"
git commit --allow-empty -q -m "remove: drop unused helpers"

echo "=== Test: no tag, mixed commits ==="

echo "--- Python ---"
PY_OUT=$(mktemp)
python3 "$DIR/changelog.py" --output "$PY_OUT" 2>&1

if [ -f "$PY_OUT" ]; then
  PY_CONTENT=$(cat "$PY_OUT")
  echo "$PY_CONTENT" | grep -q "## Added"    && pass || fail "Python: missing Added section"
  echo "$PY_CONTENT" | grep -q "## Fixed"    && pass || fail "Python: missing Fixed section"
  echo "$PY_CONTENT" | grep -q "## Changed"  && pass || fail "Python: missing Changed section"
  echo "$PY_CONTENT" | grep -q "## Removed"  && pass || fail "Python: missing Removed section"
  echo "$PY_CONTENT" | grep -q "add login"   && pass || fail "Python: missing feat commit"
  echo "$PY_CONTENT" | grep -q "off-by-one"  && pass || fail "Python: missing fix commit"
  echo "$PY_CONTENT" | grep -q "update depend" && pass || fail "Python: missing chore commit"
  echo "$PY_CONTENT" | grep -q "drop unused" && pass || fail "Python: missing remove commit"
else
  fail "Python: no output file generated"
fi

echo "--- Bash ---"
SH_OUT=$(mktemp)
bash "$DIR/changelog.sh" "$SH_OUT" 2>&1

if [ -f "$SH_OUT" ]; then
  SH_CONTENT=$(cat "$SH_OUT")
  echo "$SH_CONTENT" | grep -q "## Added"    && pass || fail "Bash: missing Added section"
  echo "$SH_CONTENT" | grep -q "## Fixed"    && pass || fail "Bash: missing Fixed section"
  echo "$SH_CONTENT" | grep -q "## Changed"  && pass || fail "Bash: missing Changed section"
  echo "$SH_CONTENT" | grep -q "## Removed"  && pass || fail "Bash: missing Removed section"
  echo "$SH_CONTENT" | grep -q "add login"   && pass || fail "Bash: missing feat commit"
  echo "$SH_CONTENT" | grep -q "off-by-one"  && pass || fail "Bash: missing fix commit"
  echo "$SH_CONTENT" | grep -q "update depend" && pass || fail "Bash: missing chore commit"
  echo "$SH_CONTENT" | grep -q "drop unused" && pass || fail "Bash: missing remove commit"
else
  fail "Bash: no output file generated"
fi

echo ""
echo "=== Test: with tag ==="
git tag v1.0.0
git commit --allow-empty -q -m "feat: add search feature"
git commit --allow-empty -q -m "fix: resolve timeout"
git commit --allow-empty -q -m "chore: bump version to 1.1.0"

PY_OUT2=$(mktemp)
python3 "$DIR/changelog.py" --output "$PY_OUT2" 2>&1
PC2=$(cat "$PY_OUT2")
echo "$PC2" | grep -q "add search"      && pass || fail "Python tag: missing new feature commit"
echo "$PC2" | grep -q "resolve timeout" && pass || fail "Python tag: missing fix commit"
echo "$PC2" | grep -q "bump version"    && pass || fail "Python tag: missing chore commit"
echo "$PC2" | grep -q "login page"      && fail "Python tag: included pre-tag commit" || pass

SH_OUT2=$(mktemp)
bash "$DIR/changelog.sh" "$SH_OUT2" 2>&1
SC2=$(cat "$SH_OUT2")
echo "$SC2" | grep -q "add search"      && pass || fail "Bash tag: missing new feature commit"
echo "$SC2" | grep -q "login page"      && fail "Bash tag: included pre-tag commit" || pass

echo ""
echo "=== Test: --limit flag ==="
PY_OUT3=$(mktemp)
python3 "$DIR/changelog.py" --output "$PY_OUT3" --limit 1 2>&1
PC3=$(cat "$PY_OUT3")
echo "$PC3" | grep -q "bump version" && pass || fail "Python --limit: should show most recent commit only"

echo ""
echo "=== Test: empty range (tag at HEAD, no new commits) ==="
TAG_REPO=$(mktemp -d)
cd "$TAG_REPO"
git init -q
git config user.email "test@test.com"
git config user.name "Test"
git commit --allow-empty -q -m "feat: first"
git tag v1.0.0

PY_OUT4=$(mktemp)
python3 "$DIR/changelog.py" --output "$PY_OUT4" 2>&1
PC4=$(cat "$PY_OUT4")
echo "$PC4" | grep -q "No new commits" && pass || fail "Python empty: should say no new commits"

SH_OUT4=$(mktemp)
bash "$DIR/changelog.sh" "$SH_OUT4" 2>&1
SC4=$(cat "$SH_OUT4")
echo "$SC4" | grep -q "No new commits" && pass || fail "Bash empty: should say no new commits"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ] || exit 1
