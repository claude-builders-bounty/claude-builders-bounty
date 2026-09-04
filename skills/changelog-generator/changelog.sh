#!/bin/bash
#
# changelog.sh — Generate CHANGELOG.md from git history
# Usage: bash changelog.sh [--from TAG] [--to REF] [-o FILE] [--dry-run] [--no-tag]
#

set -euo pipefail

# --- Config ---
FROM_TAG=""
TO_REF="HEAD"
OUTPUT_FILE="CHANGELOG.md"
DRY_RUN=0
NO_TAG=0
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo .)"

# --- Parse args ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    --from) FROM_TAG="$2"; shift 2 ;;
    --to) TO_REF="$2"; shift 2 ;;
    -o|--output) OUTPUT_FILE="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --no-tag) NO_TAG=1; shift ;;
    -h|--help)
      echo "Usage: $0 [--from TAG] [--to REF] [-o FILE] [--dry-run] [--no-tag]"
      exit 0
      ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

cd "$REPO_ROOT"

# --- Find last tag if not specified ---
if [[ -z "$FROM_TAG" ]]; then
  FROM_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
  if [[ -z "$FROM_TAG" ]]; then
    # No tags yet — use first commit
    FROM_TAG=$(git rev-list --max-parents=0 HEAD 2>/dev/null || echo "")
    if [[ -z "$FROM_TAG" ]]; then
      echo "ERROR: Cannot determine starting point (no tags, no commits)"
      exit 1
    fi
    UNTAGGED=1
  else
    UNTAGGED=0
  fi
else
  UNTAGGED=0
fi

# --- Get version for header ---
if [[ $UNTAGGED -eq 1 ]]; then
  VERSION="[Unreleased]"
elif git describe --tags --exact-match "$TO_REF" >/dev/null 2>&1; then
  VERSION="[$TO_REF] ($(date +%Y-%m-%d))"
else
  VERSION="[Unreleased]"
fi

# --- Date ---
TODAY=$(date +%Y-%m-%d)

# --- Categorize commit ---
categorize() {
  local msg="$1"
  local lower_msg
  lower_msg=$(echo "$msg" | tr '[:upper:]' '[:lower:]')
  
  if [[ "$lower_msg" =~ (security|cve|vulnerabilit|auth ) ]]; then
    echo "Security"
  elif [[ "$lower_msg" =~ (doc|readme|comment|typo|spell|changelog ) ]]; then
    echo "Docs"
  elif [[ "$lower_msg" =~ (add|create|new|implement|introduce|feature ) ]]; then
    echo "Added"
  elif [[ "$lower_msg" =~ (fix|bug|patch|resolve|hotfix ) ]]; then
    echo "Fixed"
  elif [[ "$lower_msg" =~ (remove|delete|deprecat|drop ) ]]; then
    echo "Removed"
  elif [[ "$lower_msg" =~ (update|modify|refactor|improve|optim|change|upgrade|migrate|enhance ) ]]; then
    echo "Changed"
  else
    echo "Changed"
  fi
}

# --- Generate ---
{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project will be documented in this file."
  echo ""
  echo "## $VERSION - $TODAY"
  echo ""

  # Get commits
  mapfile -t COMMITS < <(git log "$FROM_TAG".."$TO_REF" --pretty=format:"%H|%s|%an" --reverse 2>/dev/null || true)
  
  if [[ ${#COMMITS[@]} -eq 0 ]]; then
    echo "No changes since $FROM_TAG."
  else
    # Declare associative arrays for categories
    declare -A CATEGORY_ITEMS
    
    for commit in "${COMMITS[@]}"; do
      IFS='|' read -r hash msg author <<< "$commit"
      category=$(categorize "$msg")
      
      # Shorten hash to 7 chars
      short_hash="${hash:0:7}"
      
      # Append to category
      if [[ -n "${CATEGORY_ITEMS[$category]:-}" ]]; then
        CATEGORY_ITEMS[$category]="${CATEGORY_ITEMS[$category]}"$'\n'"- $msg ($short_hash)"
      else
        CATEGORY_ITEMS[$category]="- $msg ($short_hash)"
      fi
    done
    
    # Output in standard order
    for cat in Added Fixed Changed Removed Security Docs; do
      if [[ -n "${CATEGORY_ITEMS[$cat]:-}" ]]; then
        echo "### $cat"
        echo "${CATEGORY_ITEMS[$cat]}"
        echo ""
      fi
    done
  fi
  
  # Count stats
  TOTAL=${#COMMITS[@]}
  AUTHORS=$(git log "$FROM_TAG".."$TO_REF" --pretty=format:"%an" | sort -u | wc -l)
  echo "---"
  echo "*$TOTAL commit(s) by $AUTHORS contributor(s)*"
  
} > "$OUTPUT_FILE.tmp"

# --- Output or write ---
if [[ $DRY_RUN -eq 1 ]]; then
  cat "$OUTPUT_FILE.tmp"
  rm -f "$OUTPUT_FILE.tmp"
else
  mv "$OUTPUT_FILE.tmp" "$OUTPUT_FILE"
  echo "✅ CHANGELOG generated: $OUTPUT_FILE ($TOTAL commits)"
  
  # Optionally create a new tag
  if [[ $NO_TAG -eq 0 && $UNTAGGED -eq 0 ]]; then
    NEW_TAG=$(echo "$VERSION" | grep -oP '\d+\.\d+\.\d+' || echo "")
    if [[ -n "$NEW_TAG" ]]; then
      # Suggest next patch version
      IFS='.' read -r major minor patch <<< "$NEW_TAG"
      NEXT_PATCH=$((patch + 1))
      SUGGESTED_TAG="${major}.${minor}.${NEXT_PATCH}"
      echo "💡 Consider tagging: git tag -a v${SUGGESTED_TAG} -m 'Release v${SUGGESTED_TAG}'"
    fi
  fi
fi
