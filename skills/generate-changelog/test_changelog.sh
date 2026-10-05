#!/usr/bin/env bash
# test_changelog.sh — tests for changelog.sh (real execution, no mocks).
set -uo pipefail

SCRIPT="$(cd "$(dirname "$0")" && pwd)/changelog.sh"
PASS=0; FAIL=0

# 测试产生的临时目录统一清理
TRACK="$(mktemp)"
cleanup() {
    while IFS= read -r t; do
        [[ -n "$t" ]] && rm -rf "$t"
    done < "$TRACK"
    rm -f "$TRACK"
}
trap cleanup EXIT

ok()   { PASS=$((PASS+1)); echo "ok   $1"; }
bad()  { FAIL=$((FAIL+1)); echo "FAIL $1"; }

make_repo() {
    local d; d="$(mktemp -d)"
    printf '%s\n' "$d" >> "$TRACK"
    git -C "$d" init -q
    git -C "$d" config user.email t@t.t
    git -C "$d" config user.name t
    printf '%s' "$d"
}

commit() { git -C "$1" commit -q --allow-empty -m "$2"; }

# --- 1. conventional commits land in the right buckets ---
d="$(make_repo)"
commit "$d" "initial commit"; git -C "$d" tag v0.1.0
commit "$d" "feat: add user authentication"
commit "$d" "fix: resolve null pointer on login"
commit "$d" "docs: update readme"
commit "$d" "remove deprecated legacy API"
commit "$d" "BREAKING CHANGE: rename config format"
out="$(bash "$SCRIPT" --repo "$d" --output "$d/C.md")"
grep -q "### Added" "$d/C.md" \
  && grep -A3 "### Added" "$d/C.md" | grep -q "add user authentication" \
  && ok "feat -> Added" || bad "feat -> Added"
grep -A3 "### Fixed" "$d/C.md" | grep -q "null pointer" \
  && ok "fix -> Fixed" || bad "fix -> Fixed"
grep -A3 "### Removed" "$d/C.md" | grep -q "deprecated legacy API" \
  && ok "remove -> Removed" || bad "remove -> Removed"
grep -A6 "### Changed" "$d/C.md" | grep -q "BREAKING CHANGE" \
  && ok "breaking -> Changed" || bad "breaking -> Changed"

# --- 2. merge noise filtered ---
d2="$(make_repo)"
commit "$d2" "a"; git -C "$d2" tag v0
commit "$d2" "Merge branch 'feature-x'"
commit "$d2" "feat: real work"
bash "$SCRIPT" --repo "$d2" --output "$d2/C.md" >/dev/null
! grep -q "Merge branch" "$d2/C.md" \
  && ok "merge noise filtered" || bad "merge noise filtered"

# --- 3. --since flag respected ---
d3="$(make_repo)"
commit "$d3" "v1 work"; git -C "$d3" tag v1.0.0
commit "$d3" "feat: v2 feature"
bash "$SCRIPT" --repo "$d3" --since v1.0.0 --output "$d3/C.md" >/dev/null
grep -q "v2 feature" "$d3/C.md" && ! grep -q "v1 work" "$d3/C.md" \
  && ok "--since respected" || bad "--since respected"

# --- 4. empty range ---
d4="$(make_repo)"
commit "$d4" "x"; git -C "$d4" tag v9.9.9
bash "$SCRIPT" --repo "$d4" --output "$d4/C.md" >/dev/null
grep -q "No changes found" "$d4/C.md" \
  && ok "empty range message" || bad "empty range message"

# --- 5. not a git repo -> error ---
d5="$(mktemp -d)"; printf '%s\n' "$d5" >> "$TRACK"
bash "$SCRIPT" --repo "$d5" --output "$d5/C.md" >/dev/null 2>&1
[[ $? -ne 0 ]] && ok "non-repo errors out" || bad "non-repo errors out"

# --- 6. repo without tags -> full history ---
d6="$(make_repo)"
commit "$d6" "feat: lonely commit"
bash "$SCRIPT" --repo "$d6" --output "$d6/C.md" >/dev/null
grep -q "lonely commit" "$d6/C.md" \
  && ok "tagless repo uses full history" || bad "tagless repo uses full history"

# --- 7. breaking marker (!) -> Changed, marker kept ---
d7="$(make_repo)"
commit "$d7" "a"; git -C "$d7" tag v0
commit "$d7" "feat!: drop v1 API"
bash "$SCRIPT" --repo "$d7" --output "$d7/C.md" >/dev/null
grep -A3 "### Changed" "$d7/C.md" | grep -q "⚠️.*drop v1 API" \
  && ok "feat! -> Changed with marker" || bad "feat! -> Changed with marker"

# --- 8. keyword order: fix beats remov ---
d8="$(make_repo)"
commit "$d8" "a"; git -C "$d8" tag v0
commit "$d8" "fix broken remove command"
bash "$SCRIPT" --repo "$d8" --output "$d8/C.md" >/dev/null
grep -A3 "### Fixed" "$d8/C.md" | grep -q "broken remove command" \
  && ok "fix beats remov" || bad "fix beats remov"

# --- 9. --since nonexistent tag -> error ---
d9="$(make_repo)"
commit "$d9" "a"
bash "$SCRIPT" --repo "$d9" --since v9.9.9-nope --output "$d9/C.md" >/dev/null 2>&1
[[ $? -ne 0 ]] && ok "bad --since errors out" || bad "bad --since errors out"

# --- 13. relative --output resolved against invocation dir, not --repo ---
d13="$(make_repo)"
commit "$d13" "a"; git -C "$d13" tag v0
commit "$d13" "feat: h1 check"
mkdir -p "$d13/work"
( cd "$d13/work" && bash "$SCRIPT" --repo "$d13" --output rel.md >/dev/null )
[[ -f "$d13/work/rel.md" ]] && grep -q "h1 check" "$d13/work/rel.md" \
  && ok "relative --output uses cwd" || bad "relative --output uses cwd"

# --- 14. option value that looks like another option -> error ---
d14="$(make_repo)"
commit "$d14" "a"
err="$(bash "$SCRIPT" --repo "$d14" --output --since 2>&1 >/dev/null)"
[[ $? -ne 0 && "$err" == *"requires a value"* ]] \
  && ok "option-like value rejected" || bad "option-like value rejected"

# --- 15. unknown "word:" prefix is not stripped ---
d15="$(make_repo)"
commit "$d15" "a"; git -C "$d15" tag v0
commit "$d15" "important: do not deploy on Friday"
bash "$SCRIPT" --repo "$d15" --output "$d15/C.md" >/dev/null
grep -q "important: do not deploy on Friday" "$d15/C.md" \
  && ok "unknown prefix preserved" || bad "unknown prefix preserved"

echo
echo "passed: $PASS, failed: $FAIL"
[[ $FAIL -eq 0 ]]
