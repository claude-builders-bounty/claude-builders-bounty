#!/usr/bin/env bash
set -euo pipefail

# Generate a Keep a Changelog-style CHANGELOG.md from git history.
# Usage:
#   bash changelog.sh [output-file]
#   bash changelog.sh --since <ref> [output-file]
#   bash changelog.sh --repo <path> [output-file]

OUTPUT="CHANGELOG.md"
REPO="."
SINCE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      REPO="${2:?--repo requires a path}"
      shift 2
      ;;
    --since)
      SINCE="${2:?--since requires a git ref}"
      shift 2
      ;;
    -o|--output)
      OUTPUT="${2:?--output requires a file path}"
      shift 2
      ;;
    -h|--help)
      cat <<'HELP'
Generate CHANGELOG.md from git history.

Usage:
  bash changelog.sh [output-file]
  bash changelog.sh --output CHANGELOG.md
  bash changelog.sh --since v1.2.0 --output CHANGELOG.md
  bash changelog.sh --repo /path/to/repo --output CHANGELOG.md

Behavior:
  - Finds commits since the latest git tag by default.
  - If no tags exist, uses all commits.
  - Categorizes commits into Added, Fixed, Changed, and Removed.
  - Writes a Markdown CHANGELOG.md file.
HELP
      exit 0
      ;;
    *)
      OUTPUT="$1"
      shift
      ;;
  esac
done

if ! git -C "$REPO" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: $REPO is not a git repository" >&2
  exit 1
fi

if [[ -z "$SINCE" ]]; then
  if SINCE_TAG=$(git -C "$REPO" describe --tags --abbrev=0 2>/dev/null); then
    SINCE="$SINCE_TAG"
  fi
fi

if [[ -n "$SINCE" ]]; then
  RANGE="$SINCE..HEAD"
  RANGE_LABEL="since $SINCE"
else
  RANGE="HEAD"
  RANGE_LABEL="all history"
fi

TMP_COMMITS=$(mktemp)
TMP_BODY=$(mktemp)
trap 'rm -f "$TMP_COMMITS" "$TMP_BODY"' EXIT

# Use ASCII unit separator between fields to preserve spaces in subjects.
git -C "$REPO" log "$RANGE" --no-merges --date=short --pretty=format:'%h%x1f%ad%x1f%s' > "$TMP_COMMITS" || true

DATE=$(date +%Y-%m-%d)
REPO_NAME=$(basename "$(git -C "$REPO" rev-parse --show-toplevel)")

categorize() {
  local subject_lc="$1"
  case "$subject_lc" in
    remove:*|removed:*|delete:*|deleted:*|deprecate:*|deprecated:*|*" remove "*|*" delete "*|*" drop "*)
      printf 'Removed'
      ;;
    fix:*|fixed:*|bug:*|bugfix:*|hotfix:*|patch:*|*" fix "*|*" fixes "*|*" fixed "*|*" bug "*)
      printf 'Fixed'
      ;;
    feat:*|feature:*|add:*|added:*|new:*|*" add "*|*" adds "*|*" added "*|*" introduce "*|*" introduces "*)
      printf 'Added'
      ;;
    change:*|changed:*|update:*|updated:*|refactor:*|perf:*|docs:*|test:*|chore:*|ci:*|style:*|build:*|*" update "*|*" change "*|*" refactor "*)
      printf 'Changed'
      ;;
    *)
      printf 'Changed'
      ;;
  esac
}

for category in Added Fixed Changed Removed; do
  printf '##CATEGORY:%s\n' "$category" >> "$TMP_BODY"
done

if [[ ! -s "$TMP_COMMITS" ]]; then
  cat > "$OUTPUT" <<EOF
# Changelog

All notable changes to $REPO_NAME are documented in this file.

## [Unreleased] - $DATE

_No commits found for $RANGE_LABEL._
EOF
  echo "Wrote $OUTPUT (no commits found for $RANGE_LABEL)"
  exit 0
fi

while IFS=$'\x1f' read -r hash commit_date subject || [[ -n "${hash:-}" ]]; do
  [[ -n "${hash:-}" ]] || continue
  subject_lc=$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')
  category=$(categorize "$subject_lc")
  printf '%s\t- %s (`%s`, %s)\n' "$category" "$subject" "$hash" "$commit_date" >> "$TMP_BODY"
done < "$TMP_COMMITS"

{
  printf '# Changelog\n\n'
  printf 'All notable changes to %s are documented in this file.\n\n' "$REPO_NAME"
  printf 'Generated from git history: %s.\n\n' "$RANGE_LABEL"
  printf '## [Unreleased] - %s\n\n' "$DATE"
  for category in Added Fixed Changed Removed; do
    printf '### %s\n\n' "$category"
    if grep -q "^$category"$'\t' "$TMP_BODY"; then
      grep "^$category"$'\t' "$TMP_BODY" | cut -f2-
    else
      printf '_No entries._\n'
    fi
    printf '\n'
  done
} > "$OUTPUT"

echo "Wrote $OUTPUT from $RANGE_LABEL"
