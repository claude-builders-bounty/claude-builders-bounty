#!/usr/bin/env bash
set -euo pipefail

# Generate a structured CHANGELOG.md from git history since the last tag.
# Usage: bash changelog.sh [--output FILE] [--tag TAG]

OUTPUT="CHANGELOG.md"
SINCE_TAG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output) OUTPUT="$2"; shift 2 ;;
    --tag)    SINCE_TAG="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash changelog.sh [--output FILE] [--tag TAG]"
      echo "  --output  Output file (default: CHANGELOG.md)"
      echo "  --tag     Generate since this tag (default: latest tag)"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "Error: not inside a git repository" >&2
  exit 1
fi

if [[ -z "$SINCE_TAG" ]]; then
  SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

REPO_NAME=$(basename "$(git rev-parse --show-toplevel)")
TODAY=$(date +%Y-%m-%d)

if [[ -n "$SINCE_TAG" ]]; then
  RANGE="${SINCE_TAG}..HEAD"
  HEADER="## [$REPO_NAME] — Changes since $SINCE_TAG ($TODAY)"
else
  RANGE=""
  HEADER="## [$REPO_NAME] — Full Changelog ($TODAY)"
fi

classify_commit() {
  local msg="$1"
  local lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

  if echo "$lower" | grep -qE '^(feat|add|new|create|implement|introduce|support)'; then
    echo "Added"
  elif echo "$lower" | grep -qE '^(fix|bug|patch|resolve|correct|repair|hotfix)'; then
    echo "Fixed"
  elif echo "$lower" | grep -qE '^(remove|delete|drop|deprecate|strip|clean)'; then
    echo "Removed"
  else
    echo "Changed"
  fi
}

declare -A CATEGORIES
CATEGORIES[Added]=""
CATEGORIES[Fixed]=""
CATEGORIES[Changed]=""
CATEGORIES[Removed]=""

while IFS='|' read -r hash subject author; do
  [[ -z "$hash" ]] && continue
  category=$(classify_commit "$subject")
  CATEGORIES[$category]+="- $subject (\`${hash:0:7}\` by $author)"$'\n'
done < <(git log $RANGE --pretty=format:'%H|%s|%an' --no-merges)

{
  echo "# Changelog"
  echo ""
  echo "$HEADER"
  echo ""

  for cat in Added Fixed Changed Removed; do
    if [[ -n "${CATEGORIES[$cat]}" ]]; then
      echo "### $cat"
      echo "${CATEGORIES[$cat]}"
    fi
  done
} > "$OUTPUT"

TOTAL=0
for cat in Added Fixed Changed Removed; do
  if [[ -n "${CATEGORIES[$cat]}" ]]; then
    count=$(echo -n "${CATEGORIES[$cat]}" | grep -c '^-' || true)
    TOTAL=$((TOTAL + count))
  fi
done

echo "✅ Generated $OUTPUT with $TOTAL entries"
echo "   Categories: $(for cat in Added Fixed Changed Removed; do [[ -n "${CATEGORIES[$cat]}" ]] && echo -n "$cat "; done)"
