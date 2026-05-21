#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [output_file] [--tag <tag>] [--all]

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
SINCE_TAG=""
ALL=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tag)   SINCE_TAG="$2"; shift 2 ;;
    --all)   ALL=true; shift ;;
    -o)      OUTPUT="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash changelog.sh [output_file] [--tag <tag>] [--all]"
      echo "  --tag <tag>   Generate changelog since this tag"
      echo "  --all         Generate changelog for all commits"
      echo "  -o <file>     Output file (default: CHANGELOG.md)"
      exit 0 ;;
    *)       OUTPUT="$1"; shift ;;
  esac
done

if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "Error: not inside a git repository" >&2
  exit 1
fi

# Determine range
if [[ "$ALL" == true ]]; then
  RANGE=""
  RANGE_LABEL="All history"
elif [[ -n "$SINCE_TAG" ]]; then
  RANGE="${SINCE_TAG}..HEAD"
  RANGE_LABEL="Since ${SINCE_TAG}"
else
  LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
  if [[ -n "$LATEST_TAG" ]]; then
    RANGE="${LATEST_TAG}..HEAD"
    RANGE_LABEL="Since ${LATEST_TAG}"
  else
    RANGE=""
    RANGE_LABEL="All history (no tags found)"
  fi
fi

# Fetch commits
if [[ -n "$RANGE" ]]; then
  COMMITS=$(git log "$RANGE" --pretty=format:"%s|||%h|||%an|||%ad" --date=short 2>/dev/null || true)
else
  COMMITS=$(git log --pretty=format:"%s|||%h|||%an|||%ad" --date=short 2>/dev/null || true)
fi

if [[ -z "$COMMITS" ]]; then
  echo "No commits found in range: $RANGE_LABEL" >&2
  exit 0
fi

# Parse and categorize
declare -A ENTRIES

while IFS=$'\n' read -r line; do
  subject=$(echo "$line" | cut -d'|' -f1)
  hash=$(echo "$line" | cut -d'|' -f4 | tr -d ' ')
  author=$(echo "$line" | cut -d'|' -f7 | tr -d ' ')
  date=$(echo "$line" | cut -d'|' -f10 | tr -d ' ')

  [[ -z "$subject" ]] && continue

  # Skip merge commits
  if [[ "$subject" =~ ^Merge ]]; then
    continue
  fi

  prefix=""
  desc="$subject"

  # Match conventional commit: prefix(optional-scope): description
  # Use sed to extract prefix
  extracted=$(echo "$subject" | sed -n 's/^\([a-zA-Z]*\)([^)]*):[[:space:]]*\(.*\)/\1|||\2/p')
  if [[ -n "$extracted" ]]; then
    prefix=$(echo "$extracted" | cut -d'|' -f1 | tr '[:upper:]' '[:lower:]')
    desc=$(echo "$extracted" | cut -d'|' -f4)
  else
    # Try without scope: prefix: description
    extracted=$(echo "$subject" | sed -n 's/^\([a-zA-Z]*\):[[:space:]]*\(.*\)/\1|||\2/p')
    if [[ -n "$extracted" ]]; then
      prefix=$(echo "$extracted" | cut -d'|' -f1 | tr '[:upper:]' '[:lower:]')
      desc=$(echo "$extracted" | cut -d'|' -f4)
    fi
  fi

  entry="- ${desc} (\`${hash}\`) — ${author} ${date}"

  cat_name=""
  case "$prefix" in
    feat|add)          cat_name="Added" ;;
    fix|bugfix|hotfix) cat_name="Fixed" ;;
    remove|delete|drop|deprecate) cat_name="Removed" ;;
    refactor|docs|perf|style|chore|ci|test|build|change|update) cat_name="Changed" ;;
  esac

  # Fallback: keyword matching
  if [[ -z "$cat_name" ]]; then
    lower_subject=$(echo "$subject" | tr '[:upper:]' '[:lower:]')
    if [[ "$lower_subject" == *"add "* ]] || [[ "$lower_subject" == *"new "* ]] || [[ "$lower_subject" == *"introduce "* ]]; then
      cat_name="Added"
    elif [[ "$lower_subject" == *"fix "* ]] || [[ "$lower_subject" == *"bugfix "* ]] || [[ "$lower_subject" == *"patch "* ]]; then
      cat_name="Fixed"
    elif [[ "$lower_subject" == *"remov "* ]] || [[ "$lower_subject" == *"delet "* ]] || [[ "$lower_subject" == *"drop "* ]]; then
      cat_name="Removed"
    elif [[ "$lower_subject" == *"update "* ]] || [[ "$lower_subject" == *"change "* ]] || [[ "$lower_subject" == *"refactor "* ]] || [[ "$lower_subject" == *"improve "* ]]; then
      cat_name="Changed"
    else
      cat_name="Changed"
    fi
  fi

  ENTRIES["$cat_name"]+="${entry}"$'\n'

done <<< "$COMMITS"

# Build output
TODAY=$(date +%Y-%m-%d)

{
  echo "# Changelog"
  echo ""
  echo "## [Unreleased] — ${TODAY}"
  echo ""
  echo "_${RANGE_LABEL}_"
  echo ""

  for category in "Added" "Fixed" "Changed" "Removed"; do
    content="${ENTRIES[$category]:-}"
    if [[ -n "$content" ]]; then
      echo "### ${category}"
      echo ""
      echo -n "$content"
      echo ""
    fi
  done
} > "$OUTPUT"

echo "✓ Changelog written to: $OUTPUT"
echo "  Range: $RANGE_LABEL"
COMMIT_COUNT=$(echo "$COMMITS" | wc -l | tr -d ' ')
echo "  Commits processed: $COMMIT_COUNT"
