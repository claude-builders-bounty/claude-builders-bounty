#!/usr/bin/env bash
set -euo pipefail

# Changelog generator from Git history
# Usage: ./changelog.sh [--output CHANGELOG.md] [--since <tag|commit>]

OUTPUT_FILE="CHANGELOG.md"
SINCE=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --output|-o)
      OUTPUT_FILE="$2"
      shift 2
      ;;
    --since|-s)
      SINCE="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: Not a git repository." >&2
  exit 1
fi

# Detect latest git tag if --since not provided
if [ -z "$SINCE" ]; then
  LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
  if [ -n "$LAST_TAG" ]; then
    RANGE="${LAST_TAG}..HEAD"
    TARGET_VERSION="Unreleased (since ${LAST_TAG})"
  else
    RANGE="HEAD"
    TARGET_VERSION="Initial Release"
  fi
else
  RANGE="${SINCE}..HEAD"
  TARGET_VERSION="Unreleased (since ${SINCE})"
fi

CURRENT_DATE=$(date +%Y-%m-%d)

# Temporary storage for commit categories
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT

touch "$TMP_DIR/added.txt"
touch "$TMP_DIR/fixed.txt"
touch "$TMP_DIR/changed.txt"
touch "$TMP_DIR/removed.txt"
touch "$TMP_DIR/other.txt"

# Process git log: hash|subject
if [ "$RANGE" = "HEAD" ]; then
  LOG_COMMITS=$(git log --pretty=format:"%h|%s")
else
  LOG_COMMITS=$(git log "$RANGE" --pretty=format:"%h|%s")
fi

if [ -z "$LOG_COMMITS" ]; then
  echo "No new commits found in range: $RANGE"
  exit 0
fi

while IFS='|' read -r HASH SUBJECT; do
  [ -z "$SUBJECT" ] && continue
  
  # Normalize subject
  CLEAN_SUBJ=$(echo "$SUBJECT" | sed -E 's/^[a-zA-Z0-9_-]+(\([^)]+\))?:\s*//')
  ENTRY="- ${CLEAN_SUBJ} (\`${HASH}\`)"
  
  # Categorize based on Conventional Commits or keywords
  if [[ "$SUBJECT" =~ ^(feat|add)(\(.*\))?:|[Aa]dd|[Ff]eature|[Nn]ew ]]; then
    echo "$ENTRY" >> "$TMP_DIR/added.txt"
  elif [[ "$SUBJECT" =~ ^(fix|bugfix)(\(.*\))?:|[Ff]ix|[Bb]ug|[Pp]atch ]]; then
    echo "$ENTRY" >> "$TMP_DIR/fixed.txt"
  elif [[ "$SUBJECT" =~ ^(refactor|perf|style|docs|chore|change|update)(\(.*\))?:|[Cc]hange|[Uu]pdate|[Rr]efactor ]]; then
    echo "$ENTRY" >> "$TMP_DIR/changed.txt"
  elif [[ "$SUBJECT" =~ ^(revert|remove|deprecate)(\(.*\))?:|[Rr]emove|[Dd]elete|[Dd]eprecat ]]; then
    echo "$ENTRY" >> "$TMP_DIR/removed.txt"
  else
    echo "$ENTRY" >> "$TMP_DIR/other.txt"
  fi
done <<< "$LOG_COMMITS"

# Build new changelog block
HEADER="## [${TARGET_VERSION}] - ${CURRENT_DATE}"

CONTENT="${HEADER}\n\n"

if [ -s "$TMP_DIR/added.txt" ]; then
  CONTENT="${CONTENT}### Added\n$(cat "$TMP_DIR/added.txt")\n\n"
fi

if [ -s "$TMP_DIR/fixed.txt" ]; then
  CONTENT="${CONTENT}### Fixed\n$(cat "$TMP_DIR/fixed.txt")\n\n"
fi

if [ -s "$TMP_DIR/changed.txt" ]; then
  CONTENT="${CONTENT}### Changed\n$(cat "$TMP_DIR/changed.txt")\n\n"
fi

if [ -s "$TMP_DIR/removed.txt" ]; then
  CONTENT="${CONTENT}### Removed\n$(cat "$TMP_DIR/removed.txt")\n\n"
fi

if [ -s "$TMP_DIR/other.txt" ]; then
  CONTENT="${CONTENT}### Other Changes\n$(cat "$TMP_DIR/other.txt")\n\n"
fi

# Write or prepend to CHANGELOG.md
if [ -f "$OUTPUT_FILE" ]; then
  # Prepend under the main title if exists
  TMP_OUT=$(mktemp)
  if grep -q "^# Changelog" "$OUTPUT_FILE"; then
    awk -v content="$CONTENT" '
      /^# Changelog/ { print; print ""; printf "%s", content; next }
      { print }
    ' "$OUTPUT_FILE" > "$TMP_OUT"
  else
    echo -e "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n${CONTENT}" > "$TMP_OUT"
    cat "$OUTPUT_FILE" >> "$TMP_OUT"
  fi
  mv "$TMP_OUT" "$OUTPUT_FILE"
else
  echo -e "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n${CONTENT}" > "$OUTPUT_FILE"
fi

echo "Successfully generated/updated ${OUTPUT_FILE}"
