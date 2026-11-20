#!/usr/bin/env bash
# Unit tests for changelog.sh: builds a throwaway git repo and asserts
# categorization, tag cutoff, overrides, and the no-clobber guard.
set -uo pipefail

SCRIPT="$(cd "$(dirname "$0")" && pwd)/changelog.sh"
PASS=0 FAIL=0

check() { # check <description> <command...>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then PASS=$((PASS+1)); echo "PASS: $desc"
  else FAIL=$((FAIL+1)); echo "FAIL: $desc"; fi
}

refute() { # refute <description> <command...> — command must NOT succeed
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then FAIL=$((FAIL+1)); echo "FAIL: $desc"
  else PASS=$((PASS+1)); echo "PASS: $desc"; fi
}

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

repo="$tmp/repo"
git init -q "$repo"
git -C "$repo" config user.email t@t.t && git -C "$repo" config user.name tester
c() { git -C "$repo" commit -q --allow-empty -m "$1"; }

# Commits before the tag (must NOT appear in default output):
c "feat: core engine"
c "fix: startup crash"
git -C "$repo" tag v1.0.0
# Commits after the tag (must be categorized correctly):
c "feat: add logout button"
c "fix(login): handle empty password"
c "remove legacy flag parsing"
c "drop support for Node 16"
c "revert: undo dropdown rename"
c "bump dependencies to latest"
c "chore: tidy imports"

OUT="$tmp/out.md"

# --- default run: since last tag -------------------------------------------------
check "runs clean (since last tag)" bash "$SCRIPT" -o "$OUT" "$repo"
check "has Unreleased header" grep -q '^## \[Unreleased\]' "$OUT"
check "lists all 7 post-tag commits" \
  bash -c '[ "$(grep -c "^- " "'"$OUT"'")" -eq 7 ]'
refute "excludes pre-tag commit (core engine)" grep -q 'core engine' "$OUT"
refute "excludes pre-tag commit (startup crash)" grep -q 'startup crash' "$OUT"
check "names the tag cutoff" grep -q 'since `v1.0.0`' "$OUT"
check "every bullet carries a short sha" \
  bash -c '! grep "^- " "'"$OUT"'" | grep -vE "\([0-9a-f]{7,}\)$"'

# --- categorization: bullets must sit under the right heading --------------------
in_section() { awk -v sec="### $1" -v pat="$2" '
  $0==sec {inside=1; next}
  /^### / || /^## / {inside=0}
  inside && index($0,pat) {found=1}
  END {exit !found}' "$OUT"; }
check "Added: feat: add logout button" in_section Added "add logout button"
check "Fixed: fix(login): empty password" in_section Fixed "handle empty password"
check "Removed: remove legacy flag" in_section Removed "remove legacy flag"
check "Removed: drop Node 16" in_section Removed "drop support for Node 16"
check "Removed: revert prefix wins over 'dropdown'" in_section Removed "undo dropdown rename"
check "Changed: bump dependencies" in_section Changed "bump dependencies"
check "Changed: chore default bucket" in_section Changed "tidy imports"

# --- overrides and guards ---------------------------------------------------------
ALL="$tmp/all.md"
check "--no-tag includes pre-tag commits" bash "$SCRIPT" --no-tag -o "$ALL" "$repo"
check "--no-tag output has core engine" grep -q 'core engine' "$ALL"
check "--no-tag says full history" grep -q 'Full history' "$ALL"

SINCE="$tmp/since.md"
check "--since HEAD~2 runs" bash "$SCRIPT" --since HEAD~2 -o "$SINCE" "$repo"
check "--since HEAD~2 keeps exactly 2 commits" \
  bash -c '[ "$(grep -c "^- " "'"$SINCE"'")" -eq 2 ]'
refute "--since excludes older ones" grep -q 'logout button' "$SINCE"

HAND="$tmp/hand.md"
echo "# My hand-written changelog" > "$HAND"
refute "refuses to clobber hand-written file" bash "$SCRIPT" -o "$HAND" "$repo"
check "hand-written content untouched" grep -q 'hand-written changelog' "$HAND"
check "-f forces overwrite" bash "$SCRIPT" -f -o "$HAND" "$repo"
check "-f output is generated" grep -q 'generated-by: changelog.sh' "$HAND"
check "regenerating own output works (marker present)" \
  bash "$SCRIPT" -o "$HAND" "$repo"

refute "rejects non-repo dir" bash "$SCRIPT" -o /dev/null "$tmp"

echo "----------------------------------------"
echo "changelog.sh tests: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
