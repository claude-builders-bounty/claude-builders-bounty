#!/usr/bin/env bash
# changelog.sh — generate a structured CHANGELOG.md from git history.
#
# Usage:
#   bash changelog.sh                 # commits since last tag -> CHANGELOG.md
#   bash changelog.sh v1.2.0          # commits since a specific tag
#   bash changelog.sh "" OUT.md      # custom output file
#   bash changelog.sh v1.2.0 OUT.md  # both
#
# Zero dependencies beyond git. Categorizes conventional commits
# (feat/fix/chore/refactor/remove/...) and falls back to keyword heuristics.
set -euo pipefail

FROM_TAG="${1:-}"
OUT="${2:-CHANGELOG.md}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: not a git repository" >&2
  exit 1
fi

if [ -z "$FROM_TAG" ]; then
  FROM_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
fi

if [ -n "$FROM_TAG" ]; then
  RANGE="$FROM_TAG..HEAD"
  VERSION="$FROM_TAG"
else
  RANGE="HEAD"
  VERSION="Unreleased"
fi

TODAY=$(date +%Y-%m-%d)

added=()
fixed=()
changed=()
removed=()

categorize() {
  # $1 = short hash, $2 = subject
  local hash="$1" subject="$2" bucket
  local lower
  lower=$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')
  case "$lower" in
    feat*|add*|support*|implement*) bucket=added ;;
    fix*|bug*|patch*|hotfix*|repair*) bucket=fixed ;;
    remove*|delete*|drop*|revert*|deprecate*) bucket=removed ;;
    *) bucket=changed ;;
  esac
  case "$bucket" in
    added)   added+=("- \`${hash}\` ${subject}") ;;
    fixed)   fixed+=("- \`${hash}\` ${subject}") ;;
    removed) removed+=("- \`${hash}\` ${subject}") ;;
    *)       changed+=("- \`${hash}\` ${subject}") ;;
  esac
}

# here-string instead of process substitution: works identically on Git-Bash/MSYS (Windows), where '< <(...)' can silently produce nothing
commits=$(git log "$RANGE" --no-merges --pretty=format:'%h%x09%s' || true)
while IFS=$'\t' read -r hash subject; do
  [ -n "$hash" ] || continue
  categorize "$hash" "$subject"
done <<< "$commits"

section() {
  local title="$1"; shift
  local items=() x
  for x in "$@"; do [ -n "$x" ] && items+=("$x"); done
  [ ${#items[@]} -eq 0 ] && return 0
  printf '\n### %s\n\n' "$title"
  printf '%s\n' "${items[@]}"
}

{
  printf '# Changelog\n\n'
  printf 'All notable changes to this project.\n\n'
  printf '## %s — %s\n' "$VERSION" "$TODAY"
  section "Added"   "${added[@]-}"
  section "Fixed"   "${fixed[@]-}"
  section "Changed" "${changed[@]-}"
  section "Removed" "${removed[@]-}"
} > "$OUT"

echo "wrote $OUT ($(wc -l < "$OUT") lines) — range: ${RANGE}"
