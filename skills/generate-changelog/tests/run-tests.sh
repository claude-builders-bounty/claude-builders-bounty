#!/usr/bin/env bash
# Self-contained test suite for changelog.sh. Creates throwaway repos in a temp dir.
set -uo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$HERE/changelog.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
PASS=0; FAIL=0

check() { # name, condition
  if [ "$2" -eq 0 ]; then PASS=$((PASS+1)); printf '  ok   %s\n' "$1";
  else FAIL=$((FAIL+1)); printf '  FAIL %s\n' "$1"; fi
}

newrepo() {
  local d="$TMP/$1"; mkdir -p "$d"
  ( cd "$d" && git init -q && git config user.email t@t.t && git config user.name test ) >/dev/null 2>&1
  echo "$d"
}

echo "changelog.sh tests"

# 1. Categorisation with a tag
R=$(newrepo t1); cd "$R" || exit 1; echo a > f; git add .; git commit -qm "chore: init"; git tag v1.0.0
echo b >> f; git commit -qam "feat: add widget"
echo c >> f; git commit -qam "fix: correct typo"
echo d >> f; git commit -qam "refactor: split module"
echo e >> f; git commit -qam "remove: drop old flag"
bash "$SCRIPT" --out CHANGELOG.md >/dev/null 2>&1
grep -q "### Added" CHANGELOG.md && grep -q "add widget" CHANGELOG.md; check "categories Added" $?
grep -q "### Fixed" CHANGELOG.md; check "categories Fixed" $?
grep -q "### Removed" CHANGELOG.md; check "categories Removed" $?
grep -q "### Changed" CHANGELOG.md; check "categories Changed" $?
grep -q "\[Unreleased\]" CHANGELOG.md; check "Unreleased heading" $?

# 2. No tags: every commit included
R=$(newrepo t2); cd "$R" || exit 1; echo x > f; git add .; git commit -qm "feat: first feature"
bash "$SCRIPT" --out CH.md >/dev/null 2>&1
grep -q "first feature" CH.md; check "no-tag repo includes root commit" $?

# 3. --version override
bash "$SCRIPT" --version 2.0.0 --out CH2.md >/dev/null 2>&1
grep -q "\[2.0.0\]" CH2.md; check "--version override" $?

# 4. --from explicit ref
R=$(newrepo t3); cd "$R" || exit 1; echo a > f; git add .; git commit -qm "feat: one"; git tag v0.1.0
echo b >> f; git commit -qam "feat: two"
bash "$SCRIPT" --from v0.1.0 --out C.md >/dev/null 2>&1
grep -q "two" C.md && ! grep -q "one  " C.md; check "--from respected" $?

# 5. Idempotent: second run on the same range does not duplicate the entry
bash "$SCRIPT" --out C.md >/dev/null 2>&1
before=$(grep -c "## \[" C.md)
bash "$SCRIPT" --out C.md >/dev/null 2>&1
after=$(grep -c "## \[" C.md)
[ "$before" -eq "$after" ]; check "idempotent second run" $?

# 6. Non-git directory fails cleanly
mkdir -p "$TMP/nogit"; cd "$TMP/nogit"
bash "$SCRIPT" --out X.md >/dev/null 2>&1; [ $? -ne 0 ]; check "rejects non-git dir" $?

# 7. Existing CHANGELOG is prepended, not overwritten
R=$(newrepo t4); cd "$R" || exit 1; echo a > f; git add .; git commit -qm "feat: new work"
printf '# Changelog\n\n## [1.0.0] - 2020-01-01\n\n### Added\n- old entry\n' > CHANGELOG.md
bash "$SCRIPT" --out CHANGELOG.md >/dev/null 2>&1
grep -q "old entry" CHANGELOG.md && grep -q "new work" CHANGELOG.md; check "prepends, keeps history" $?

echo
echo "passed: $PASS  failed: $FAIL"
[ "$FAIL" -eq 0 ]