#!/usr/bin/env bash
# Regression tests for changelog.sh
# Run: bash skills/generate-changelog/tests/test_changelog.sh

set -eo pipefail
SCRIPT="$(cd "$(dirname "$0")/.." && pwd)/changelog.sh"
PASS=0; FAIL=0

ok()  { echo "  ✅ $1"; (( PASS++ )) || true; }
fail(){ echo "  ❌ $1"; (( FAIL++ )) || true; }

check() {
  local desc="$1" expected="$2" actual="$3"
  if echo "$actual" | grep -qF "$expected"; then ok "$desc"
  else fail "$desc — expected: '$expected'  got: '$actual'"; fi
}

check_absent() {
  local desc="$1" pattern="$2" actual="$3"
  if echo "$actual" | grep -qF "$pattern"; then fail "$desc — '$pattern' should not appear"
  else ok "$desc"; fi
}

# ── Set up a temp git repo ────────────────────────────────────────────────────
REPO="$(mktemp -d)"
trap 'rm -rf "$REPO"' EXIT
cd "$REPO"
git init -q
git config user.email "test@test.com"
git config user.name "Test"

commit() {
  echo "$RANDOM" > file.txt
  git add file.txt
  git commit -q -m "$1"
}

echo ""
echo "━━━ changelog.sh regression tests ━━━"

# ── Section 1: classify function — via preview output ────────────────────────
echo ""
echo "▶  Commit classification"

commit "feat: add login page"
commit "fix: null pointer on submit"
commit "remove: delete legacy endpoint"
commit "docs: update README"

out="$(bash "$SCRIPT" --preview)"

check "feat: → Added section"     "### ✨ Added"   "$out"
check "fix: → Fixed section"      "### 🐛 Fixed"   "$out"
check "remove: → Removed section" "### 🗑️ Removed" "$out"
check "docs: → Changed section"   "### 🔧 Changed" "$out"

# ── Section 2: feature keyword variants (must use conventional format type: msg) ──
echo ""
echo "▶  Keyword variant classification"

git tag v0.0.0

commit "add: new dashboard widget"
commit "implement: export functionality"
commit "introduce: rate limiting"
commit "feature: dark mode"

out="$(bash "$SCRIPT" --since v0.0.0 --preview)"
check "add: → Added"       "### ✨ Added" "$out"
check "implement: → Added" "Export functionality" "$out"
check "introduce: → Added" "Rate limiting" "$out"
check "feature: → Added"   "Dark mode" "$out"

# ── Section 3: fix keyword variants ──────────────────────────────────────────
echo ""
echo "▶  Fix keyword variants"

git tag v0.1.0
commit "bugfix: crash on empty input"
commit "hotfix: payment race condition"
commit "patch: off-by-one in pagination"

out="$(bash "$SCRIPT" --since v0.1.0 --preview)"
check "bugfix → Fixed" "### 🐛 Fixed" "$out"
check "hotfix → Fixed" "Payment race condition" "$out"
check "patch → Fixed"  "Off-by-one in pagination" "$out"

# ── Section 4: remove keyword variants ───────────────────────────────────────
echo ""
echo "▶  Remove keyword variants"

git tag v0.2.0
commit "delete: deprecated /v1 API"
commit "deprecate: xml export"
commit "drop: IE11 support"
commit "revert: bad migration"

out="$(bash "$SCRIPT" --since v0.2.0 --preview)"
check "delete → Removed"    "### 🗑️ Removed" "$out"
check "deprecate → Removed" "Xml export" "$out"
check "drop → Removed"      "IE11 support" "$out"
check "revert → Removed"    "Bad migration" "$out"

# ── Section 5: message cleaning ──────────────────────────────────────────────
echo ""
echo "▶  Message cleaning"

git tag v0.3.0
commit "feat(auth): add OAuth2 support"
commit "fix!: breaking change in token format"
commit "feat(ui): new sidebar"

out="$(bash "$SCRIPT" --since v0.3.0 --preview)"
check    "scope stripped"            "Add OAuth2 support"              "$out"
check    "breaking ! stripped"       "Breaking change in token format" "$out"
check_absent "scope not in output"  "(auth)"                          "$out"
check_absent "exclamation in output" "fix!"                           "$out"

# ── Section 6: --preview does not write file ─────────────────────────────────
echo ""
echo "▶  --preview flag"

git tag v0.4.0
commit "feat: test preview flag"

bash "$SCRIPT" --since v0.4.0 --preview > /dev/null
if [[ ! -f "CHANGELOG.md" ]]; then ok "--preview does not create file"
else fail "--preview should not create CHANGELOG.md"; fi

# ── Section 7: file output ────────────────────────────────────────────────────
echo ""
echo "▶  File output"

bash "$SCRIPT" --since v0.4.0 --version "1.0.0"
[[ -f "CHANGELOG.md" ]]              && ok "CHANGELOG.md created"     || fail "CHANGELOG.md not created"
grep -q "## \[1.0.0\]" CHANGELOG.md && ok "--version label in file"  || fail "--version label missing"
grep -q "# Changelog"  CHANGELOG.md && ok "# Changelog header added"  || fail "header missing"

# ── Section 8: prepend to existing file ─────────────────────────────────────
echo ""
echo "▶  Prepend to existing CHANGELOG.md"

git tag v1.0.0
commit "feat: second release feature"
bash "$SCRIPT" --since v1.0.0 --version "2.0.0"

head_line="$(head -1 CHANGELOG.md)"
[[ "$head_line" == "# Changelog" ]]       && ok "Header preserved at top"   || fail "Header not at top"
grep -q "## \[2.0.0\]" CHANGELOG.md      && ok "New release prepended"     || fail "New release missing"
grep -q "## \[1.0.0\]" CHANGELOG.md      && ok "Old release still present" || fail "Old release overwritten"
new_line="$(grep -n "## \[2.0.0\]" CHANGELOG.md | cut -d: -f1)"
old_line="$(grep -n "## \[1.0.0\]" CHANGELOG.md | cut -d: -f1)"
[[ "$new_line" -lt "$old_line" ]]         && ok "Newer release appears first" || fail "Release order wrong"

# ── Section 9: --output flag ─────────────────────────────────────────────────
echo ""
echo "▶  --output flag"

git tag v2.0.0
commit "feat: custom output path"

bash "$SCRIPT" --since v2.0.0 --output RELEASE.md
[[ -f "RELEASE.md" ]] && ok "--output creates custom file" || fail "--output file not created"

# ── Section 10: --since flag ─────────────────────────────────────────────────
echo ""
echo "▶  --since flag"

git tag v3.0.0
commit "feat: only this should appear"
commit "feat: and this one too"
git tag v4.0.0
commit "feat: post-v4 commit only"

out="$(bash "$SCRIPT" --since v4.0.0 --preview)"
check       "--since includes post-tag"   "Post-v4 commit only"      "$out"
check_absent "--since excludes pre-tag"   "Only This Should Appear"  "$out"

# ── Section 11: no-tags fallback ─────────────────────────────────────────────
echo ""
echo "▶  Full history fallback (no tags)"

NOTAG="$(mktemp -d)"
cd "$NOTAG"
git init -q
git config user.email "test@test.com"
git config user.name "Test"
echo "x" > a.txt; git add .; git commit -q -m "feat: first ever commit"
echo "y" > b.txt; git add .; git commit -q -m "fix: first ever fix"

out="$(bash "$SCRIPT" --preview)"
check "fallback Added section" "### ✨ Added" "$out"
check "fallback Fixed section" "### 🐛 Fixed" "$out"
rm -rf "$NOTAG"
cd "$REPO"

# ── Section 12: empty commit range ───────────────────────────────────────────
echo ""
echo "▶  Empty commit range"

git tag v5.0.0
msg="$(bash "$SCRIPT" --since v5.0.0 --preview 2>&1 || true)"
check "empty range exits with message" "No commits" "$msg"

# ── Section 13: non-git directory guard ──────────────────────────────────────
echo ""
echo "▶  Non-git directory guard"

NOTGIT="$(mktemp -d)"
err="$(cd "$NOTGIT" && bash "$SCRIPT" --preview 2>&1 || true)"
rm -rf "$NOTGIT"
check "non-git error" "Not a git repository" "$err"

# ── Section 14: --version override ───────────────────────────────────────────
echo ""
echo "▶  --version flag"

git tag v6.0.0
commit "fix: version override test"

out="$(bash "$SCRIPT" --since v6.0.0 --version "99.0.0" --preview)"
check "--version overrides auto-detected tag" "## [99.0.0]" "$out"

# ── Section 15: stdout summary line ──────────────────────────────────────────
echo ""
echo "▶  Stdout summary on write"

git tag v7.0.0
commit "feat: summary output test"

summary="$(bash "$SCRIPT" --since v7.0.0 --version "8.0.0" 2>&1)"
check "summary shows commit count" "1 commits" "$summary"
check "summary shows filename"     "CHANGELOG.md" "$summary"

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
TOTAL=$(( PASS + FAIL ))
echo "Results: ${PASS}/${TOTAL} passed"
if [[ "$FAIL" -gt 0 ]]; then
  echo "❌ ${FAIL} test(s) failed"
  exit 1
else
  echo "✅ All tests passing"
fi
