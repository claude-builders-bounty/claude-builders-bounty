#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history.
set -euo pipefail

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: not inside a git repository." >&2
  exit 1
fi

FROM_TAG="${1:-}"
TO_REF="${2:-HEAD}"

if [ -z "$FROM_TAG" ]; then
  FROM_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

if [ -z "$FROM_TAG" ]; then
  RANGE="HEAD"
  RANGE_LABEL="all history (no tags found)"
else
  RANGE="${FROM_TAG}..${TO_REF}"
  RANGE_LABEL="${FROM_TAG} → ${TO_REF}"
fi

COMMITS=$(git log "$RANGE" --pretty=format:"%s" --no-merges)

if [ -z "$COMMITS" ]; then
  echo "No commits found in range: $RANGE_LABEL" >&2
  exit 0
fi

ADDED=()
FIXED=()
CHANGED=()
REMOVED=()

while IFS= read -r line; do
  [ -z "$line" ] && continue
  prefix=$(echo "$line" | grep -oE '^[a-zA-Z]+' || echo "")
  prefix_lower=$(echo "$prefix" | tr '[:upper:]' '[:lower:]')
  message=$(echo "$line" | sed -E 's/^[a-zA-Z]+(\([^)]*\))?!?:[[:space:]]*//')

  case "$prefix_lower" in
    feat|feature|add|added)
      ADDED+=("$message") ;;
    fix|fixed|bugfix|hotfix)
      FIXED+=("$message") ;;
    refactor|change|changed|perf|style|chore|build|ci)
      CHANGED+=("$message") ;;
    remove|removed|revert|drop)
      REMOVED+=("$message") ;;
    *)
      lower_line=$(echo "$line" | tr '[:upper:]' '[:lower:]')
      if echo "$lower_line" | grep -qE '\b(add|added|adds|new|introduce)\b'; then
        ADDED+=("$line")
      elif echo "$lower_line" | grep -qE '\b(fix|fixed|fixes|bug|resolve|resolved)\b'; then
        FIXED+=("$line")
      elif echo "$lower_line" | grep -qE '\b(remove|removed|removes|delete|deleted|drop|dropped)\b'; then
        REMOVED+=("$line")
      else
        CHANGED+=("$line")
      fi
      ;;
  esac
done <<< "$COMMITS"

DATE=$(date +%Y-%m-%d)
TMP_FILE=$(mktemp)

{
  echo "## [Unreleased] - ${DATE}"
  echo "_Range: ${RANGE_LABEL}_"
  echo ""
  if [ ${#ADDED[@]} -gt 0 ]; then
    echo "### Added"
    for item in "${ADDED[@]}"; do echo "- ${item}"; done
    echo ""
  fi
  if [ ${#FIXED[@]} -gt 0 ]; then
    echo "### Fixed"
    for item in "${FIXED[@]}"; do echo "- ${item}"; done
    echo ""
  fi
  if [ ${#CHANGED[@]} -gt 0 ]; then
    echo "### Changed"
    for item in "${CHANGED[@]}"; do echo "- ${item}"; done
    echo ""
  fi
  if [ ${#REMOVED[@]} -gt 0 ]; then
    echo "### Removed"
    for item in "${REMOVED[@]}"; do echo "- ${item}"; done
    echo ""
  fi
} > "$TMP_FILE"

if [ -f CHANGELOG.md ]; then
  { echo "# Changelog"; echo ""; cat "$TMP_FILE"; tail -n +2 CHANGELOG.md; } > CHANGELOG.md.new
  mv CHANGELOG.md.new CHANGELOG.md
else
  { echo "# Changelog"; echo ""; cat "$TMP_FILE"; } > CHANGELOG.md
fi

rm -f "$TMP_FILE"
echo "CHANGELOG.md written for range: ${RANGE_LABEL}"