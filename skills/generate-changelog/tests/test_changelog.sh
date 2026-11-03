#!/usr/bin/env bash
# Self-contained tests for changelog.sh. Runs git in a temporary repository.
# Usage: bash tests/test_changelog.sh
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
SCRIPT="$HERE/../changelog.sh"
PASS=0
FAIL=0

ok()   { PASS=$((PASS + 1)); printf '  ok   %s\n' "$1"; }
fail() { FAIL=$((FAIL + 1)); printf '  FAIL %s\n     expected: %s\n     got:      %s\n' "$1" "$2" "$3"; }
contains() { # contains <name> <needle> <hay>
  if grep -qF -- "$2" <<<"$3"; then ok "$1"; else fail "$1" "output to contain: $2" "$3"; fi
}
absent() { # absent <name> <needle> <hay>
  if grep -qF -- "$2" <<<"$3"; then fail "$1" "output must not contain: $2" "$3"; else ok "$1"; fi
}

mkrepo() { # mkrepo <dir> — initialise a throwaway repository
  rm -rf "$1"; mkdir -p "$1"
  git -C "$1" init -q
  git -C "$1" config user.email tester@example.com
  git -C "$1" config user.name Tester
  git -C "$1" config commit.gpgsign false
}

commit() { # commit <repo> <message>
  git -C "$1" commit -q --allow-empty -m "$2"
}

run() { # run <outfile> [args...] — generate into <outfile> and echo its content
  local out="$1"; shift
  bash "$SCRIPT" --out "$out" "$@" >/dev/null 2>&1 || true
  [ -s "$out" ] && cat "$out"
}

echo "changelog.sh tests"

# ── categorisation of conventional and plain messages ──────────────────────
WORK="$(mktemp -d)"
mkrepo "$WORK/repo"
commit "$WORK/repo" "feat(api): add export endpoint"
commit "$WORK/repo" "fix: crash on empty input"
commit "$WORK/repo" "refactor(core): rename sampler"
commit "$WORK/repo" "chore: tidy scripts"
commit "$WORK/repo" "remove legacy migration path"
commit "$WORK/repo" "Add dark mode"
commit "$WORK/repo" "Fix flaky timeout test"
commit "$WORK/repo" "Update the README badge"
OUT="$(run "$WORK/CHANGELOG.md" --repo "$WORK/repo")"

contains "feat → Added"            "### Added"      "$OUT"
contains "feat subject kept"       "Add export endpoint" "$OUT"
contains "fix → Fixed"             "### Fixed"      "$OUT"
contains "fix subject kept"        "Crash on empty input" "$OUT"
contains "refactor → Changed"      "### Changed"    "$OUT"
contains "refactor scope stripped" "Rename sampler" "$OUT"
contains "chore → Changed"         "Tidy scripts"   "$OUT"
contains "plain add → Added"       "Add dark mode"      "$OUT"
contains "plain fix → Fixed"       "Fix flaky timeout test" "$OUT"
contains "plain update → Changed"  "Update the README badge" "$OUT"
contains "plain remove → Removed"  "### Removed"    "$OUT"
contains "remove subject kept"     "Remove legacy migration path" "$OUT"

# ── merge commits are excluded ─────────────────────────────────────────────
mkrepo "$WORK/merges"
commit "$WORK/merges" "feat: base"
git -C "$WORK/merges" checkout -q -b feature
commit "$WORK/merges" "feat: branch work"
git -C "$WORK/merges" checkout -q master 2>/dev/null || git -C "$WORK/merges" checkout -q main
git -C "$WORK/merges" merge -q --no-ff feature -m "Merge pull request #1 from feature" 2>/dev/null
OUT="$(run "$WORK/m.md" --repo "$WORK/merges")"
absent "merge commit excluded" "Merge pull request" "$OUT"
contains "branch commit kept" "Branch work" "$OUT"

# ── commits since the last tag only ────────────────────────────────────────
mkrepo "$WORK/tagged"
commit "$WORK/tagged" "feat: first"
commit "$WORK/tagged" "fix: second"
git -C "$WORK/tagged" tag v1.0.0
commit "$WORK/tagged" "feat: after tag"
commit "$WORK/tagged" "docs: post-tag notes"
OUT="$(run "$WORK/t.md" --repo "$WORK/tagged")"
contains "post-tag feat listed"      "After tag"       "$OUT"
contains "post-tag docs listed"      "Post-tag notes"  "$OUT"
absent  "pre-tag feat not listed"    "First"           "$OUT"
absent  "pre-tag fix not listed"     "Second"          "$OUT"
contains "default range is just Unreleased" "## [Unreleased]" "$OUT"
absent  "default range has no (since" "(since"          "$OUT"

# ── explicit --from labels the range, --out writes where asked ─────────────
OUT="$(run "$WORK/all.md" --repo "$WORK/tagged" --from v1.0.0)"
contains "explicit from keeps range label" "since v1.0.0" "$OUT"
[ -s "$WORK/all.md" ] && ok "--out writes the given file" || fail "--out writes the given file" "file exists" "missing"

# ── no-tag repository includes the whole history ───────────────────────────
mkrepo "$WORK/untagged"
commit "$WORK/untagged" "feat: alpha"
commit "$WORK/untagged" "fix: beta"
OUT="$(run "$WORK/u.md" --repo "$WORK/untagged")"
contains "no-tag repo covers all history" "Alpha" "$OUT"
contains "no-tag repo is Unreleased"      "## [Unreleased]" "$OUT"

# ── empty range fails loudly instead of writing an empty changelog ─────────
WORK2="$(mktemp -d)"; mkrepo "$WORK2/repo"
commit "$WORK2/repo" "feat: only"
if bash "$SCRIPT" --repo "$WORK2/repo" --from HEAD --out "$WORK2/empty.md" >/dev/null 2>&1; then
  fail "empty range exits non-zero" "non-zero" "0"
else
  ok "empty range exits non-zero"
fi
[ -s "$WORK2/empty.md" ] && fail "empty range writes no file" "no file" "file written" || ok "empty range writes no file"

# ── duplicate subjects appear once ─────────────────────────────────────────
mkrepo "$WORK/dupes"
commit "$WORK/dupes" "chore: bump version"
commit "$WORK/dupes" "chore: bump version"
commit "$WORK/dupes" "feat: real work"
OUT="$(run "$WORK/d.md" --repo "$WORK/dupes")"
contains "dedupe keeps one" "Bump version" "$OUT"
n="$(grep -c 'Bump version' <<<"$OUT")"
check_dupes() { [ "$n" -eq 1 ]; }
check_dupes && ok "duplicate subjects appear once" || fail "duplicate subjects appear once" "1 occurrence" "$n occurrences"

rm -rf "$WORK" "$WORK2"

printf '%d passed, %d failed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
