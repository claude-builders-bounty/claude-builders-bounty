#!/usr/bin/env bash
# Tests for changelog.sh — builds throwaway git repos and asserts classification.
# Run: bash tests/test_changelog.sh   (exit 0 = all pass, 1 = failure)
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$HERE/../changelog.sh"
pass=0
fail=0

check() {
	if [ "$2" = "1" ]; then
		pass=$((pass + 1)); printf 'PASS %s\n' "$1"
	else
		fail=$((fail + 1)); printf 'FAIL %s\n' "$1"
	fi
}

mkrepo() {
	local dir="$1"
	rm -rf "$dir"
	mkdir -p "$dir"
	git -C "$dir" init -q
	git -C "$dir" config user.email t@t
	git -C "$dir" config user.name t
}

# --- Test 1: each category is recognized (conventional commits with scope) ---
R1="$(mktemp -d)"
mkrepo "$R1"
git -C "$R1" commit -q --allow-empty -m "chore: initial commit"
git -C "$R1" tag v1.0.0
git -C "$R1" commit -q --allow-empty -m "feat(api): add pagination"
git -C "$R1" commit -q --allow-empty -m "fix(ui): correct off-by-one"
git -C "$R1" commit -q --allow-empty -m "refactor: split parser"
git -C "$R1" commit -q --allow-empty -m "remove: drop legacy endpoint"
OUT1="$(bash "$SCRIPT" --repo "$R1" --dry-run)"
printf '%s' "$OUT1" | grep -q -- "- feat(api): add pagination" && check "feat(scope) -> Added" 1 || check "feat(scope) -> Added" 0
printf '%s' "$OUT1" | awk '/^### Fixed/{f=1} /^### Changed/{f=0} f && /off-by-one/' | grep -q . && check "fix(scope) -> Fixed" 1 || check "fix(scope) -> Fixed" 0
printf '%s' "$OUT1" | awk '/^### Changed/{f=1} /^### Removed/{f=0} f && /split parser/' | grep -q . && check "refactor -> Changed" 1 || check "refactor -> Changed" 0
printf '%s' "$OUT1" | awk '/^### Removed/{f=1} f && /legacy endpoint/' | grep -q . && check "remove -> Removed" 1 || check "remove -> Removed" 0

# --- Test 2: range starts at the last tag (pre-tag commit excluded) ---
printf '%s' "$OUT1" | grep -q "initial commit" && check "commits before tag are excluded" 0 || check "commits before tag are excluded" 1

# --- Test 3: --since overrides tag detection ---
OUT3="$(bash "$SCRIPT" --repo "$R1" --since v1.0.0 --version v1.1.0 --dry-run)"
printf '%s' "$OUT3" | grep -q "## \[v1.1.0\]" && check "--since + --version label" 1 || check "--since + --version label" 0

# --- Test 4: no tags -> entire history ---
R2="$(mktemp -d)"
mkrepo "$R2"
git -C "$R2" commit -q --allow-empty -m "feat: first feature"
git -C "$R2" commit -q --allow-empty -m "fix: first fix"
OUT4="$(bash "$SCRIPT" --repo "$R2" --dry-run)"
printf '%s' "$OUT4" | grep -q "first feature" && printf '%s' "$OUT4" | grep -q "first fix" \
	&& check "no tags -> whole history" 1 || check "no tags -> whole history" 0

# --- Test 5: writes a file, not stdout, without --dry-run ---
R3="$(mktemp -d)"
mkrepo "$R3"
git -C "$R3" commit -q --allow-empty -m "feat: x"
(cd "$R3" && bash "$SCRIPT" >/dev/null)
[ -f "$R3/CHANGELOG.md" ] && grep -q "### Added" "$R3/CHANGELOG.md" && check "writes CHANGELOG.md" 1 || check "writes CHANGELOG.md" 0

# --- Test 6: non-git directory fails with exit 2 ---
R4="$(mktemp -d)"
bash "$SCRIPT" --repo "$R4" --dry-run >/dev/null 2>&1
[ "$?" -eq 2 ] && check "non-git dir -> exit 2" 1 || check "non-git dir -> exit 2" 0

# --- Test 7: merge commits are skipped ---
R5="$(mktemp -d)"
mkrepo "$R5"
git -C "$R5" commit -q --allow-empty -m "feat: base"
git -C "$R5" checkout -q -b side
git -C "$R5" commit -q --allow-empty -m "feat: side work"
git -C "$R5" checkout -q master 2>/dev/null || git -C "$R5" checkout -q main
git -C "$R5" merge -q --no-ff side -m "Merge branch 'side'"
OUT7="$(bash "$SCRIPT" --repo "$R5" --dry-run)"
printf '%s' "$OUT7" | grep -q "Merge branch" && check "merge commits skipped" 0 || check "merge commits skipped" 1

rm -rf "$R1" "$R2" "$R3" "$R4" "$R5"

printf 'CHANGELOG-TESTS: %d PASS, %d FAIL\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
exit 0
