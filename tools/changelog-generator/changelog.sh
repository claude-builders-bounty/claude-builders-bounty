#!/usr/bin/env bash
# =============================================================================
# changelog.sh — Structured CHANGELOG.md generator from git history
# Usage: ./changelog.sh [SINCE_TAG_OR_REF] [--version VERSION] [--output FILE]
#   Defaults: SINCE=last git tag, VERSION=auto-detected, FILE=CHANGELOG.md
# Dependencies: git (only), bash 4+
# =============================================================================
set -euo pipefail

# --- Config ---
SINCE_REF="${1:-}"
VERSION="${2:-}"
OUTPUT_FILE="${3:-CHANGELOG.md}"
CATEGORIES=("Added" "Fixed" "Changed" "Removed" "Security" "Deprecated" "Other")
declare -A KEYWORDS=(
  ["Added"]="feat|add|new|introduce|implement"
  ["Fixed"]="fix|bug|patch|hotfix|resolve|issue"
  ["Changed"]="change|update|modify|refactor|improve|optimize|tweak"
  ["Removed"]="remove|delete|drop|deprecate|cleanup"
  ["Security"]="security|cve|vuln|auth|permission|xss|injection|csrf"
  ["Deprecated"]="deprecat|legacy|obsolete"
)

# --- Auto-detect version ---
if [[ -z "$VERSION" ]]; then
  # Try to get from git describe or use date-based version
  VERSION="$(git describe --tags --abbrev=0 2>/dev/null || echo 'v0.0.0')"
  # If no tag found, generate one from date
  if [[ "$VERSION" == "v0.0.0" ]]; then
    VERSION="unreleased-$(date +%Y-%m-%d)"
  fi
fi

# --- Auto-detect since ref ---
if [[ -z "$SINCE_REF" ]]; then
  SINCE_REF="$(git describe --tags --abbrev=0 2>/dev/null || echo '')"
fi

TODAY=$(date +%Y-%m-%d)
TMPFILE=$(mktemp)
trap 'rm -f "$TMPFILE"' EXIT

# --- Build regex pattern for categorization ---
build_pattern() {
  local cat="$1"
  local words="${KEYWORDS[$cat]:-}"
  if [[ -n "$words" ]]; then
    echo "(?i)($words)"
  else
    echo "(?i)(.*)"
  fi
}

# --- Initialize category buckets ---
for cat in "${CATEGORIES[@]}"; do
  echo "" > "${TMPFILE}.${cat,,}"
done

# --- Parse commits ---
LOG_RANGE=""
if [[ -n "$SINCE_REF" ]]; then
  LOG_RANGE="${SINCE_REF}..HEAD"
else
  LOG_RANGE="HEAD"
fi

# Format: HASH|SUBJECT|BODY (first line of body)
git log "$LOG_RANGE" --pretty=format:"%h|%s|%b" --no-merges | while IFS='|' read -r hash subject body; do
  [[ -z "$hash" ]] && continue
  
  combined="$subject $body"
  categorized=false
  
  for cat in "${CATEGORIES[@]}"; do
    pattern=$(build_pattern "$cat")
    if echo "$combined" | grep -qiE "$pattern"; then
      # Extract scope: feat(scope): message → scope
      scope=""
      if echo "$subject" | grep -qE '^[a-z]+\(([^)]+)\):'; then
        scope="$(echo "$subject" | sed -E 's/^[a-z]+\(([^)]+)\):.*/[\1]/')"
      fi
      echo "- ${subject} (\`${hash}\`) ${scope}" >> "${TMPFILE}.${cat,,}"
      categorized=true
      break
    fi
  done
  
  if [[ "$categorized" == false ]]; then
    echo "- ${subject} (\`${hash}\`)" >> "${TMPFILE}.other"
  fi
done

# --- Generate CHANGELOG.md ---
{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project are documented in this file."
  echo ""
  
  # Header for this version
  echo "## [${VERSION}] - ${TODAY}"
  echo ""
  
  has_content=false
  for cat in "${CATEGORIES[@]}"; do
    bucket="${TMPFILE}.${cat,,}"
    if [[ -s "$bucket" ]]; then
      has_content=true
        echo "### ${cat}"
        echo ""
        sort "$bucket"
        echo ""
    fi
  done
  
  if [[ "$has_content" == false ]]; then
    echo "_No changes since ${SINCE_REF:-beginning of time}_"
    echo ""
  fi
  
  # Stats line
  total_commits=$(git log "$LOG_RANGE" --oneline --no-merges 2>/dev/null | wc -l)
  echo "<!-- ${total_commits} commits since ${SINCE_REF:-initial commit} -->"
  
} > "$OUTPUT_FILE"

echo "✅ CHANGELOG generated: ${OUTPUT_FILE} (${total_commits} commits, version ${VERSION})"
echo "   Since: ${SINCE_REF:-(all history)}"

# Show preview (first 20 lines)
head -20 "$OUTPUT_FILE"
