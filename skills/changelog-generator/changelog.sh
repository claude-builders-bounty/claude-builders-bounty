#!/usr/bin/env bash
set -euo pipefail

REPO_PATH="${REPO_PATH:-.}"
OUTPUT_FILE="${OUTPUT_FILE:-CHANGELOG.md}"
SINCE=""
UNRELEASED=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-path) REPO_PATH="$2"; shift 2 ;;
    --output) OUTPUT_FILE="$2"; shift 2 ;;
    --since) SINCE="$2"; shift 2 ;;
    --unreleased) UNRELEASED=true; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

cd "$REPO_PATH"

if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "Error: not a git repository: $REPO_PATH"
  exit 1
fi

if [[ -z "$SINCE" ]]; then
  LAST_TAG=$(git describe --tags --abbrev=0 2> /dev/null || true)
  if [[ -z "$LAST_TAG" ]]; then
    SINCE=$(git rev-list --max-parents=0 HEAD 2> /dev/null || echo "")
    if [[ -z "$SINCE" ]]; then
      echo "Error: no commits found in repository"
      exit 1
    fi
    echo "No tags found — using first commit as boundary."
  else
    SINCE="$LAST_TAG"
  fi
fi

if [[ "$SINCE" == "$(git rev-list --max-parents=0 HEAD 2>/dev/null || true)" ]] || $UNRELEASED; then
  HEADER_SCOPE="Unreleased"
elif [[ -n "$LAST_TAG" ]]; then
  HEADER_SCOPE="$LAST_TAG..HEAD"
else
  HEADER_SCOPE="Unreleased"
fi

COMMITS=$(git log "$SINCE"..HEAD --oneline --no-decorate 2> /dev/null || git log --oneline --no-decorate 2> /dev/null || echo "")

if [[ -z "$COMMITS" ]]; then
  echo "No new commits since $SINCE. Nothing to generate."
  exit 0
fi

declare -A SECTIONS
SECTIONS[Added]=""
SECTIONS[Fixed]=""
SECTIONS[Changed]=""
SECTIONS[Removed]=""
SECTIONS[Uncategorized]=""

DATE=$(date +%Y-%m-%d)

while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  HASH=$(echo "$line" | awk '{print $1}')
  MSG=$(echo "$line" | cut -d' ' -f2-)
  CATEGORY="Uncategorized"

  LOWER=$(echo "$MSG" | tr '[:upper:]' '[:lower:]')
  case "$LOWER" in
    feat:*|feature:*|add*|implement*|introduce*)
      CATEGORY="Added" ;;
    fix:*|bugfix:*|hotfix:*|correct*|resolve*)
      CATEGORY="Fixed" ;;
    refactor:*|perf:*|style:*|chore:*|docs:*|test:*|ci:*|build:*|update*|change*|bump*|migrate*)
      CATEGORY="Changed" ;;
    remove:*|deprecate:*|delete:*|revert:*|drop*)
      CATEGORY="Removed" ;;
  esac

  CLEAN_MSG=$(echo "$MSG" | sed -E 's/^(feat|feature|fix|bugfix|hotfix|refactor|perf|style|chore|docs|test|ci|build|remove|deprecate|delete|revert)\([^)]*\)://i' | sed -E 's/^(feat|feature|fix|bugfix|hotfix|refactor|perf|style|chore|docs|test|ci|build|remove|deprecate|delete|revert)://i' | sed 's/^ *//')
  if [[ -z "$CLEAN_MSG" ]]; then
    CLEAN_MSG=$(echo "$MSG" | sed 's/^ *//')
  fi

  SECTIONS["$CATEGORY"]+="  - $CLEAN_MSG ($HASH)"$'\n'
done <<< "$COMMITS"

{
  echo "# Changelog"
  echo ""
  echo "## [$HEADER_SCOPE] — $DATE"
  echo ""

  HAS_CONTENT=false
  for SECTION in Added Fixed Changed Removed Uncategorized; do
    CONTENT="${SECTIONS[$SECTION]}"
    if [[ -n "$CONTENT" ]]; then
      echo "### $SECTION"
      echo ""
      echo "$CONTENT" | sed '/^$/d'
      echo ""
      HAS_CONTENT=true
    fi
  done

  if ! $HAS_CONTENT; then
    echo "_No changes._"
    echo ""
  fi
} > "$OUTPUT_FILE"

echo "CHANGELOG generated → $(pwd)/$OUTPUT_FILE"