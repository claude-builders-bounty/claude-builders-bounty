#!/usr/bin/env bash
# changelog.sh — generate a structured CHANGELOG.md from git history
# Compatible with bash 3+ (macOS default) and bash 4+/5+
# Usage: bash changelog.sh [output_file] [--from <tag|sha>] [--to <tag|sha>]
set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
FROM=""
TO="HEAD"

shift || true
while [[ $# -gt 0 ]]; do
  case "$1" in
    --from) FROM="$2"; shift 2 ;;
    --to)   TO="$2";   shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

# Resolve range: default to commits since the last tag
if [[ -z "$FROM" ]]; then
  FROM=$(git describe --tags --abbrev=0 2>/dev/null || true)
fi

if [[ -z "$FROM" ]]; then
  RANGE="$TO"
  echo "No previous tag found — including all commits up to $TO."
else
  RANGE="${FROM}..${TO}"
  echo "Range: $RANGE"
fi

# Use tformat so every line has a trailing newline (avoids last-line-lost bug)
TMPFILE=$(mktemp /tmp/cl_commits.XXXXXX)
git log "$RANGE" --no-merges --pretty=tformat:"%H %s" 2>/dev/null > "$TMPFILE" || true

if [[ ! -s "$TMPFILE" ]]; then
  echo "No commits found in range ${RANGE}."
  exit 0
fi

ADDED_FILE=$(mktemp /tmp/cl_added.XXXXXX)
FIXED_FILE=$(mktemp /tmp/cl_fixed.XXXXXX)
CHANGED_FILE=$(mktemp /tmp/cl_changed.XXXXXX)
REMOVED_FILE=$(mktemp /tmp/cl_removed.XXXXXX)
OTHER_FILE=$(mktemp /tmp/cl_other.XXXXXX)

while IFS= read -r entry || [[ -n "$entry" ]]; do
  [[ -z "$entry" ]] && continue
  sha="${entry%% *}"
  subject="${entry#* }"
  # Strip conventional-commit scope: "feat(api): ..." -> "feat: ..."
  subject_clean=$(echo "$subject" | sed 's/^\([a-zA-Z]*\)([^)]*)[!]*:/\1:/')
  lower=$(echo "$subject" | tr '[:upper:]' '[:lower:]')

  if   echo "$lower" | grep -qE '^feat[^a-z]|^add(ed)?[: ]|implement[s]?[: ]|new feature'; then
    echo "- ${subject_clean} (\`${sha:0:7}\`)" >> "$ADDED_FILE"
  elif echo "$lower" | grep -qE '^fix[^a-z]|^bug[: ]|^patch[: ]|hotfix|resolve[s]?[: ]|repair'; then
    echo "- ${subject_clean} (\`${sha:0:7}\`)" >> "$FIXED_FILE"
  elif echo "$lower" | grep -qE '^(remove[d]?|drop|delet[e]?[d]?|deprecat)[: (]'; then
    echo "- ${subject_clean} (\`${sha:0:7}\`)" >> "$REMOVED_FILE"
  elif echo "$lower" | grep -qE '^(refactor|chore|style|perf|ci|build|docs|test|update|change|improv|bump|renam)[^a-z]'; then
    echo "- ${subject_clean} (\`${sha:0:7}\`)" >> "$CHANGED_FILE"
  else
    echo "- ${subject_clean} (\`${sha:0:7}\`)" >> "$OTHER_FILE"
  fi
done < "$TMPFILE"

count_lines() { wc -l < "$1" | tr -d ' '; }

DATE=$(date +%Y-%m-%d)
FROM_LABEL="${FROM:-initial commit}"

{
  echo "# Changelog"
  echo ""
  echo "## [Unreleased] — ${DATE}"
  echo ""
  echo "> Changes since \`${FROM_LABEL}\`"
  echo ""

  if [[ -s "$ADDED_FILE" ]]; then
    echo "### Added"
    cat "$ADDED_FILE"
    echo ""
  fi
  if [[ -s "$FIXED_FILE" ]]; then
    echo "### Fixed"
    cat "$FIXED_FILE"
    echo ""
  fi
  if [[ -s "$CHANGED_FILE" ]]; then
    echo "### Changed"
    cat "$CHANGED_FILE"
    echo ""
  fi
  if [[ -s "$REMOVED_FILE" ]]; then
    echo "### Removed"
    cat "$REMOVED_FILE"
    echo ""
  fi
  if [[ -s "$OTHER_FILE" ]]; then
    echo "### Other"
    cat "$OTHER_FILE"
    echo ""
  fi
} > "$OUTPUT"

TOTAL=$(( $(count_lines "$ADDED_FILE") + $(count_lines "$FIXED_FILE") + $(count_lines "$CHANGED_FILE") + $(count_lines "$REMOVED_FILE") + $(count_lines "$OTHER_FILE") ))
echo "Wrote ${OUTPUT} — ${TOTAL} commits categorised."
echo "  Added:$(count_lines "$ADDED_FILE")  Fixed:$(count_lines "$FIXED_FILE")  Changed:$(count_lines "$CHANGED_FILE")  Removed:$(count_lines "$REMOVED_FILE")  Other:$(count_lines "$OTHER_FILE")"
