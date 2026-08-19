#!/usr/bin/env bash
#
# Test suite for changelog.sh. Builds throwaway git repos in a temp directory,
# runs the generator against them, and asserts on the markdown it produces.
#
# Usage: bash tests/run_tests.sh

set -uo pipefail

SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/changelog.sh"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

passed=0
failed=0

pass() { passed=$((passed + 1)); printf '  ok   %s\n' "$1"; }
fail() {
  failed=$((failed + 1))
  printf '  FAIL %s\n' "$1"
  printf '       expected: %s\n' "$2"
  printf '       actual:   %s\n' "$3"
}

contains() { case "$2" in *"$1"*) return 0 ;; *) return 1 ;; esac; }

assert_contains() {
  if contains "$2" "$3"; then pass "$1"; else fail "$1" "output contains: $2" "it does not"; fi
}

assert_not_contains() {
  if contains "$2" "$3"; then fail "$1" "output omits: $2" "it is present"; else pass "$1"; fi
}

assert_eq() {
  if [ "$2" = "$3" ]; then pass "$1"; else fail "$1" "$2" "$3"; fi
}

# Create an isolated repo and cd into it. Commits get fixed identities and dates
# so runs are reproducible on any machine.
new_repo() {
  local dir="$WORK/$1"
  mkdir -p "$dir"
  cd "$dir" || exit 1
  git init --quiet --initial-branch=main 2>/dev/null || { git init --quiet; git checkout -q -b main 2>/dev/null; }
  git config user.email test@example.com
  git config user.name "Test Runner"
  git config commit.gpgsign false
  git config core.autocrlf false
}

commit() {
  local subject="$1" body="${2:-}"
  echo "$subject" >> log.txt
  git add -A
  if [ -n "$body" ]; then
    git commit --quiet --allow-empty -m "$subject" -m "$body"
  else
    git commit --quiet --allow-empty -m "$subject"
  fi
}

printf '\nchangelog.sh test suite\n\n'

# --------------------------------------------------------------------------
printf 'Conventional Commits map to Keep a Changelog sections\n'
new_repo categories
commit "feat: add dark mode"
commit "fix: stop crash on empty config"
commit "refactor: simplify the router"
commit "remove: drop the legacy v1 client"
commit "security: patch path traversal in upload"
commit "deprecate: mark --legacy flag for removal"
out="$($SCRIPT --stdout)"
assert_contains "feat -> Added"            "### Added"$'\n\n'"- add dark mode" "$out"
assert_contains "fix -> Fixed"             "### Fixed"$'\n\n'"- stop crash on empty config" "$out"
assert_contains "refactor -> Changed"      "### Changed"$'\n\n'"- simplify the router" "$out"
assert_contains "remove -> Removed"        "### Removed"$'\n\n'"- drop the legacy v1 client" "$out"
assert_contains "security -> Security"     "### Security" "$out"
assert_contains "deprecate -> Deprecated"  "### Deprecated" "$out"
assert_contains "sections keep Keep a Changelog order" \
  "### Added" "$(printf '%s' "$out" | head -20)"

# --------------------------------------------------------------------------
printf '\nCommit range starts at the last tag\n'
new_repo tags
commit "feat: shipped last release"
git tag v1.0.0
commit "feat: add webhook retries"
commit "fix: correct timezone parsing"
out="$($SCRIPT --stdout)"
assert_not_contains "commits before the tag are excluded" "shipped last release" "$out"
assert_contains     "commits after the tag are included"  "add webhook retries" "$out"
assert_contains     "range is reported"                   "2 commits since \`v1.0.0\`" "$out"

printf '\nTagging HEAD steps back to the previous tag\n'
git tag v1.1.0
out="$($SCRIPT --stdout)"
assert_contains "version is taken from the tag on HEAD" "## [v1.1.0] - " "$out"
assert_contains "range walks back to v1.0.0"            "since \`v1.0.0\`" "$out"
assert_contains "the compare link pins both tags" "compare/v1.0.0...v1.1.0" \
  "$($SCRIPT --stdout --repo https://github.com/acme/widgets)"

printf '\nA release named after a tag is dated by that tag\n'
new_repo dating
commit "feat: groundwork"
GIT_AUTHOR_DATE="2024-01-15T10:00:00" GIT_COMMITTER_DATE="2024-01-15T10:00:00" \
  git commit --quiet --allow-empty -m "feat: add the dated thing"
git tag v3.0.0
out="$($SCRIPT --stdout)"
assert_contains "the heading uses the tag's date, not today" "## [v3.0.0] - 2024-01-15" "$out"
out="$($SCRIPT --stdout --version 3.0.1)"
assert_contains "an explicit --version is dated today" "## [3.0.1] - $(date +%Y-%m-%d)" "$out"

printf '\nAn untagged repo falls back to full history\n'
new_repo untagged
commit "feat: first feature"
commit "fix: first bug"
out="$($SCRIPT --stdout)"
assert_contains "heading is Unreleased" "## [Unreleased]" "$out"
assert_contains "full history is used"  "2 commits — full history" "$out"

# --------------------------------------------------------------------------
printf '\nNon-conventional history is classified by its leading verb\n'
new_repo prose
commit "Add CSV export to the reports page"
commit "Fixed a memory leak in the worker pool"
commit "Removed the unused analytics bundle"
commit "Tidy up the settings screen"
commit "Rework parser so it no longer needs a fix for nested quotes"
out="$($SCRIPT --stdout)"
assert_contains "leading Add -> Added"      "- Add CSV export to the reports page" "$out"
assert_contains "leading Fixed -> Fixed"    "- Fixed a memory leak in the worker pool" "$out"
assert_contains "leading Removed -> Removed" "- Removed the unused analytics bundle" "$out"
assert_contains "unknown verb -> Changed"   "- Tidy up the settings screen" "$out"
fixed_block="$(printf '%s' "$out" | awk '/^### Fixed/{f=1;next} /^### /{f=0} f')"
assert_not_contains "a mid-sentence \"fix\" does not hijack the entry" "Rework parser" "$fixed_block"

# --------------------------------------------------------------------------
printf '\nScopes, breaking changes and PR references\n'
new_repo formatting
commit "feat(api): add cursor pagination"
commit "feat(auth)!: require PKCE for all clients"
commit "fix: reject malformed cookies" "BREAKING CHANGE: cookies without a domain are now dropped."
commit "feat: add bulk import (#412)"
out="$($SCRIPT --stdout --repo https://github.com/acme/widgets)"
assert_contains "scope is rendered"          "- **api**: add cursor pagination" "$out"
assert_contains "bang marks a breaking change" "**BREAKING** **auth**: require PKCE" "$out"
assert_contains "body trailer marks a breaking change" "**BREAKING** reject malformed cookies" "$out"
assert_contains "PR number becomes a link"   "([#412](https://github.com/acme/widgets/pull/412))" "$out"
assert_contains "compare link is generated"  "https://github.com/acme/widgets/compare/" "$(cd "$WORK/tags" && $SCRIPT --stdout --repo https://github.com/acme/widgets)"

# --------------------------------------------------------------------------
printf '\nHousekeeping commits are dropped unless --all is passed\n'
new_repo noise
commit "feat: add search"
commit "chore: bump dependencies"
commit "docs: rewrite the quickstart"
commit "ci: cache the build"
out="$($SCRIPT --stdout)"
assert_not_contains "chore is skipped" "bump dependencies" "$out"
assert_not_contains "docs is skipped"  "rewrite the quickstart" "$out"
assert_contains     "the tally still describes the whole range" "> 4 commits — full history" "$out"
assert_eq           "only the feature is listed" "1" "$(printf '%s' "$out" | grep -c '^- ')"
out="$($SCRIPT --stdout --all)"
assert_contains "--all keeps chore" "bump dependencies" "$out"
assert_contains "--all keeps docs"  "rewrite the quickstart" "$out"

# --------------------------------------------------------------------------
printf '\nDuplicate subjects are squashed\n'
new_repo dupes
commit "feat: add retry backoff"
commit "feat: add retry backoff"
out="$($SCRIPT --stdout)"
assert_eq "identical entries collapse to one" "1" \
  "$(printf '%s' "$out" | grep -c -- '- add retry backoff')"

# --------------------------------------------------------------------------
printf '\nWriting to CHANGELOG.md\n'
new_repo writing
commit "feat: add the first thing"
$SCRIPT --version 1.0.0 >/dev/null 2>&1
assert_contains "a new file gets the Keep a Changelog preamble" \
  "keepachangelog.com" "$(cat CHANGELOG.md)"
assert_contains "the release section is written" "## [1.0.0] - " "$(cat CHANGELOG.md)"
assert_contains "a one-commit tally reads as singular" "> 1 commit — full history" "$(cat CHANGELOG.md)"

commit "fix: correct the first thing"
$SCRIPT --version 1.0.1 >/dev/null 2>&1
file="$(cat CHANGELOG.md)"
assert_contains "the older release survives" "## [1.0.0] - " "$file"
assert_contains "the new release is written" "## [1.0.1] - " "$file"
assert_eq "the preamble is not duplicated" "1" "$(printf '%s' "$file" | grep -c '^# Changelog')"
assert_eq "the newest release goes on top" "## [1.0.1] - $(date +%Y-%m-%d)" \
  "$(printf '%s' "$file" | grep -m1 '^## ')"

commit "feat: add a third thing"
err="$($SCRIPT --version 1.0.1 2>&1 >/dev/null)"
assert_contains "re-running the same version is refused" "already has a section for [1.0.1]" "$err"

# --------------------------------------------------------------------------
printf '\nEdge cases\n'
new_repo empty_range
commit "feat: only commit"
git tag v2.0.0
err="$($SCRIPT --since v2.0.0 2>&1 >/dev/null)"
assert_contains "an empty range writes nothing" "nothing to write" "$err"
assert_eq "no file is created for an empty range" "no" "$([ -f CHANGELOG.md ] && echo yes || echo no)"

err="$($SCRIPT --since v9.9.9 2>&1 >/dev/null)"; rc=$?
assert_contains "an unknown ref is rejected" "unknown ref: v9.9.9" "$err"
assert_eq "an unknown ref exits non-zero" "1" "$rc"

err="$($SCRIPT --version 2>&1 >/dev/null)"; rc=$?
assert_contains "a missing option value is rejected" "--version requires a value" "$err"

err="$($SCRIPT --frobnicate 2>&1 >/dev/null)"; rc=$?
assert_contains "an unknown option is rejected" "unknown option" "$err"

mkdir -p "$WORK/not_a_repo" && cd "$WORK/not_a_repo"
err="$(GIT_CEILING_DIRECTORIES="$WORK" $SCRIPT 2>&1 >/dev/null)"
assert_contains "running outside a repo is rejected" "not inside a git repository" "$err"

new_repo quoting
commit 'feat: handle $HOME, `backticks` and "quotes" safely'
out="$($SCRIPT --stdout)"
assert_contains "shell metacharacters survive verbatim" \
  '- handle $HOME, `backticks` and "quotes" safely' "$out"

# --------------------------------------------------------------------------
printf '\n%s passed, %s failed\n\n' "$passed" "$failed"
[ "$failed" -eq 0 ]
