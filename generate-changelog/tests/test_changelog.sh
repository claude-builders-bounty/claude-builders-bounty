#!/usr/bin/env bash
# Integration tests against the real changelog.sh entry point.
# Builds a temporary git repo with a tag and known commit messages,
# then asserts CHANGELOG sections and content.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="$ROOT/changelog.sh"
WORKDIR="${TEST_WORKDIR:-$(mktemp -d)}"
KEEP_WORKDIR="${KEEP_WORKDIR:-0}"

cleanup() {
  if [[ "$KEEP_WORKDIR" != "1" ]]; then
    rm -rf "$WORKDIR"
  fi
}
trap cleanup EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }
pass() { echo "PASS: $*"; }

[[ -x "$SCRIPT" || -f "$SCRIPT" ]] || fail "missing $SCRIPT"
chmod +x "$SCRIPT"

# --- Fixture repo ---
REPO="$WORKDIR/fixture-repo"
mkdir -p "$REPO"
git -C "$REPO" init -q -b main
git -C "$REPO" config user.email "test@example.com"
git -C "$REPO" config user.name "Changelog Tester"

# Commits before tag (should NOT appear after tag range)
echo base > "$REPO/README"
git -C "$REPO" add README
git -C "$REPO" commit -q -m "chore: initial scaffold"
git -C "$REPO" tag v1.0.0

# Commits after tag — one per category
echo a > "$REPO/a.txt" && git -C "$REPO" add a.txt && git -C "$REPO" commit -q -m "feat: add export API"
echo b > "$REPO/b.txt" && git -C "$REPO" add b.txt && git -C "$REPO" commit -q -m "fix: correct null pointer in parser"
echo c > "$REPO/c.txt" && git -C "$REPO" add c.txt && git -C "$REPO" commit -q -m "refactor: simplify cache layer"
echo d > "$REPO/d.txt" && git -C "$REPO" add d.txt && git -C "$REPO" commit -q -m "remove: drop legacy config path"

OUT="$WORKDIR/CHANGELOG.md"
bash "$SCRIPT" "$OUT" "$REPO" | tee "$WORKDIR/run.log"

[[ -f "$OUT" ]] || fail "CHANGELOG not written"

# Required sections
for sec in "### Added" "### Fixed" "### Changed" "### Removed"; do
  grep -Fq "$sec" "$OUT" || fail "missing section $sec"
done
pass "all four category sections present"

# Range uses last tag
grep -Fq "v1.0.0" "$OUT" || fail "changelog should reference last tag v1.0.0"
pass "last tag referenced"

# Category placement — subjects must land in the right section
# Extract lines under each heading until next ### or EOF
extract_section() {
  local heading="$1" file="$2"
  awk -v h="$heading" '
    $0 == h {p=1; next}
    p && /^### / {exit}
    p {print}
  ' "$file"
}

added="$(extract_section "### Added" "$OUT")"
fixed="$(extract_section "### Fixed" "$OUT")"
changed="$(extract_section "### Changed" "$OUT")"
removed="$(extract_section "### Removed" "$OUT")"

echo "$added" | grep -Fq "feat: add export API" || fail "feat commit not under Added: $added"
echo "$fixed" | grep -Fq "fix: correct null pointer" || fail "fix commit not under Fixed: $fixed"
echo "$changed" | grep -Fq "refactor: simplify cache layer" || fail "refactor not under Changed: $changed"
echo "$removed" | grep -Fq "remove: drop legacy config path" || fail "remove not under Removed: $removed"
pass "commits categorized correctly"

# Pre-tag commit must not appear
if grep -Fq "initial scaffold" "$OUT"; then
  fail "pre-tag commit should not appear after v1.0.0"
fi
pass "only commits since last tag"

# Empty-repo-ish: tag at HEAD → empty sections allowed but file still valid
REPO2="$WORKDIR/empty-range"
mkdir -p "$REPO2"
git -C "$REPO2" init -q -b main
git -C "$REPO2" config user.email "test@example.com"
git -C "$REPO2" config user.name "Changelog Tester"
echo x > "$REPO2/x" && git -C "$REPO2" add x && git -C "$REPO2" commit -q -m "feat: only release"
git -C "$REPO2" tag v0.1.0
OUT2="$WORKDIR/CHANGELOG-empty.md"
bash "$SCRIPT" "$OUT2" "$REPO2" >/dev/null
grep -Fq "### Added" "$OUT2" || fail "empty range still needs Added section"
# No post-tag commits → _None_ under Added
grep -A1 "### Added" "$OUT2" | grep -Fq "_None_" || fail "expected _None_ when no commits after tag"
pass "empty range after tag produces valid empty sections"

echo ""
echo "All tests passed."
echo "OUT=$OUT"
