#!/usr/bin/env bash
#
# changelog.sh — Generate a structured CHANGELOG.md from git history.
#
# Usage: bash changelog.sh [--output PATH]
#
# Fetches commits since the last git tag (or all commits if no tag exists),
# categorizes them, and writes CHANGELOG.md.
#
set -euo pipefail

# --- Config ---------------------------------------------------------------
OUTPUT="CHANGELOG.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output|-o) OUTPUT="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash changelog.sh [--output PATH]"
      echo ""
      echo "Generates CHANGELOG.md from git history."
      echo ""
      echo "Options:"
      echo "  --output, -o PATH   Output file path (default: CHANGELOG.md)"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# --- Validate git repo ----------------------------------------------------
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "Error: Not inside a git repository." >&2
  exit 1
fi

# --- Determine range -------------------------------------------------------
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [[ -n "$LAST_TAG" ]]; then
  RANGE="${LAST_TAG}..HEAD"
  SECTION_TITLE="## [Unreleased] (since ${LAST_TAG})"
else
  RANGE="HEAD"
  SECTION_TITLE="## [Unreleased]"
fi

# --- Categorize commits ----------------------------------------------------
declare -A CATEGORIES
CATEGORIES[added]=""
CATEGORIES[fixed]=""
CATEGORIES[changed]=""
CATEGORIES[removed]=""

while IFS= read -r line; do
  [[ -z "$line" ]] && continue

  hash="${line%% *}"
  msg="${line#* }"
  short_hash="${hash:0:7}"

  # Normalize the message: strip prefix, trim
  lower_msg="$(echo "$msg" | tr '[:upper:]' '[:lower:]' | sed 's/^[[:space:]]*//')"

  # Match prefix to category
  if [[ "$lower_msg" =~ ^(add|feat|new|feature)(\(.+\))?: ]]; then
    clean="${msg#*: }"
    CATEGORIES[added]+="- ${clean} (\`${short_hash}\`)"$'\n'
  elif [[ "$lower_msg" =~ ^(fix|bug|bugfix)(\(.+\))?: ]]; then
    clean="${msg#*: }"
    CATEGORIES[fixed]+="- ${clean} (\`${short_hash}\`)"$'\n'
  elif [[ "$lower_msg" =~ ^(remove|delete|drop)(\(.+\))?: ]]; then
    clean="${msg#*: }"
    CATEGORIES[removed]+="- ${clean} (\`${short_hash}\`)"$'\n'
  elif [[ "$lower_msg" =~ ^(change|update|refactor|chore|ci|build|style|perf)(\(.+\))?: ]]; then
    clean="${msg#*: }"
    CATEGORIES[changed]+="- ${clean} (\`${short_hash}\`)"$'\n'
  else
    # No recognized prefix → Changed
    CATEGORIES[changed]+="- ${msg} (\`${short_hash}\`)"$'\n'
  fi
done < <(git log --oneline --no-merges "$RANGE" 2>/dev/null || git log --oneline --no-merges)

# --- Build output ----------------------------------------------------------
{
  echo "# Changelog"
  echo ""
  echo "$SECTION_TITLE"
  echo ""

  if [[ -n "${CATEGORIES[added]}" ]]; then
    echo "### Added"
    echo ""
    echo -n "${CATEGORIES[added]}"
    echo ""
  fi

  if [[ -n "${CATEGORIES[fixed]}" ]]; then
    echo "### Fixed"
    echo ""
    echo -n "${CATEGORIES[fixed]}"
    echo ""
  fi

  if [[ -n "${CATEGORIES[changed]}" ]]; then
    echo "### Changed"
    echo ""
    echo -n "${CATEGORIES[changed]}"
    echo ""
  fi

  if [[ -n "${CATEGORIES[removed]}" ]]; then
    echo "### Removed"
    echo ""
    echo -n "${CATEGORIES[removed]}"
    echo ""
  fi
} > "$OUTPUT"

echo "✅ Generated $OUTPUT with commits since ${LAST_TAG:-initial}"
