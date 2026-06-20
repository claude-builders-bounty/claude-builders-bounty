#!/usr/bin/env bash
set -eo pipefail

# Changelog Generator
# Generates a structured CHANGELOG.md from git history.
#
# Usage: changelog.sh [--from REF] [--to REF] [--output FILE] [--repo PATH]

FROM="${CHANGELOG_FROM:-}"
TO="${CHANGELOG_TO:-HEAD}"
OUTPUT="${CHANGELOG_OUTPUT:-CHANGELOG.md}"
REPO="${CHANGELOG_REPO:-.}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --from) FROM="$2"; shift 2 ;;
    --to) TO="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    --repo) REPO="$2"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

cd "$REPO"

if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "Error: not a git repository" >&2
  exit 1
fi

ROOT_COMMIT=$(git rev-list --max-parents=0 HEAD 2>/dev/null | head -1)

if [[ -z "$FROM" ]]; then
  LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
  if [[ -z "$LATEST_TAG" ]]; then
    FROM="$ROOT_COMMIT"
    echo "No tags found. Including all commits from initial commit." >&2
  else
    FROM="$LATEST_TAG"
    echo "Using latest tag: $LATEST_TAG" >&2
  fi
fi

if [[ "$FROM" == "$ROOT_COMMIT" ]]; then
  RANGE="$TO"
  echo "Including all commits from root commit to $TO..." >&2
else
  RANGE="${FROM}..${TO}"
  echo "Collecting commits from $FROM to $TO..." >&2
fi

declare -a ADDED FIXED CHANGED REMOVED OTHER

while IFS= read -r line; do
  HASH=$(echo "$line" | cut -d' ' -f1)
  MSG=$(echo "$line" | cut -d' ' -f2-)
  SHORT=$(git rev-parse --short "$HASH" 2>/dev/null || echo "${HASH:0:7}")

  LOWER_MSG=$(echo "$MSG" | tr '[:upper:]' '[:lower:]')

  if [[ "$LOWER_MSG" =~ ^feat(\(.+\))?!?: ]]; then
    ADDED+=("- $MSG (\`$SHORT\`)")
  elif [[ "$LOWER_MSG" =~ ^fix(\(.+\))?!?: ]]; then
    FIXED+=("- $MSG (\`$SHORT\`)")
  elif [[ "$LOWER_MSG" =~ ^(remove|delete)(\(.+\))?!?: ]]; then
    REMOVED+=("- $MSG (\`$SHORT\`)")
  elif [[ "$LOWER_MSG" =~ ^(refactor|perf|style|improve|update|upgrade|bump)(\(.+\))?!?: ]]; then
    CHANGED+=("- $MSG (\`$SHORT\`)")
  elif [[ "$LOWER_MSG" =~ ^(docs|test|chore|ci|build)(\(.+\))?!?: ]]; then
    OTHER+=("- $MSG (\`$SHORT\`)")
  else
    CHANGED+=("- $MSG (\`$SHORT\`)")
  fi
done < <(git log "$RANGE" --pretty=format:"%H %s" --no-merges 2>/dev/null)

DATE=$(date +%Y-%m-%d)

{
  echo "# Changelog"
  echo ""
  echo "## [$TO] - $DATE"
  echo ""

  if [[ ${#ADDED[@]} -gt 0 ]]; then
    echo "### Added"
    echo ""
    for entry in "${ADDED[@]}"; do
      echo "$entry"
    done
    echo ""
  fi

  if [[ ${#FIXED[@]} -gt 0 ]]; then
    echo "### Fixed"
    echo ""
    for entry in "${FIXED[@]}"; do
      echo "$entry"
    done
    echo ""
  fi

  if [[ ${#CHANGED[@]} -gt 0 ]]; then
    echo "### Changed"
    echo ""
    for entry in "${CHANGED[@]}"; do
      echo "$entry"
    done
    echo ""
  fi

  if [[ ${#REMOVED[@]} -gt 0 ]]; then
    echo "### Removed"
    echo ""
    for entry in "${REMOVED[@]}"; do
      echo "$entry"
    done
    echo ""
  fi

  TOTAL=$((${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]}))
  echo "---"
  echo ""
  echo "_Auto-generated from $TOTAL commits (from $FROM to $TO)_"
} > "$OUTPUT"

echo "Changelog written to $OUTPUT" >&2
echo "$OUTPUT"
