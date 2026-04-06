#!/usr/bin/env bash
# generate-changelog.sh — Generate structured CHANGELOG.md from git history
# Fetches commits since the last git tag and auto-categorizes them.
#
# Usage:
#   bash changelog.sh                    # Auto-detect latest tag
#   bash changelog.sh v1.0.0             # Since specific tag
#   bash changelog.sh v1.0.0 v2.0.0     # Between two tags
#   bash changelog.sh --all              # Full history (no tag filter)

set -euo pipefail

# ──────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────

OUTPUT="CHANGELOG.md"
DATE=$(date +%Y-%m-%d)
REPO_URL=$(git remote get-url origin 2>/dev/null | sed 's/\.git$//' | sed 's|git@github.com:|https://github.com/|')

# ──────────────────────────────────────────────────────────
# Parse arguments
# ──────────────────────────────────────────────────────────

FROM_TAG=""
TO_REF="HEAD"
ALL_HISTORY=false

if [[ "${1:-}" == "--all" ]]; then
  ALL_HISTORY=true
elif [[ -n "${1:-}" ]]; then
  FROM_TAG="$1"
  TO_REF="${2:-HEAD}"
else
  # Auto-detect: latest tag
  FROM_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

# Determine version for header
if [[ "$TO_REF" != "HEAD" ]]; then
  VERSION="$TO_REF"
elif [[ -n "$FROM_TAG" ]]; then
  VERSION="Unreleased (since $FROM_TAG)"
else
  VERSION="Unreleased"
fi

# Build commit range
if [[ "$ALL_HISTORY" == true ]]; then
  RANGE=""
elif [[ -n "$FROM_TAG" ]]; then
  RANGE="${FROM_TAG}..${TO_REF}"
else
  RANGE=""
fi

# ──────────────────────────────────────────────────────────
# Fetch and categorize commits
# ──────────────────────────────────────────────────────────

categorize_commit() {
  local msg="$1"
  local msg_lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

  # Added: new features, additions
  if echo "$msg_lower" | grep -qE '^(feat|add|new|create|implement|introduce|support)(\(|:|!)'; then
    echo "Added"
  elif echo "$msg_lower" | grep -qE '\b(add|added|new|create|implement|introduce)\b'; then
    echo "Added"

  # Fixed: bug fixes, patches
  elif echo "$msg_lower" | grep -qE '^(fix|bugfix|hotfix|patch|resolve|correct)(\(|:|!)'; then
    echo "Fixed"
  elif echo "$msg_lower" | grep -qE '\b(fix|fixed|bug|resolve|resolved|correct|patch)\b'; then
    echo "Fixed"

  # Removed: deletions, deprecations
  elif echo "$msg_lower" | grep -qE '^(remove|delete|deprecate|drop)(\(|:|!)'; then
    echo "Removed"
  elif echo "$msg_lower" | grep -qE '\b(remove|removed|delete|deleted|deprecate|deprecated|drop)\b'; then
    echo "Removed"

  # Changed: updates, refactors, improvements
  elif echo "$msg_lower" | grep -qE '^(refactor|update|change|improve|enhance|optimize|perf|style|chore|build|ci|docs|test)(\(|:|!)'; then
    echo "Changed"
  elif echo "$msg_lower" | grep -qE '\b(update|updated|change|changed|refactor|improve|enhanced|optimize)\b'; then
    echo "Changed"

  # Default: Changed
  else
    echo "Changed"
  fi
}

# Collect commits
declare -A CATEGORIES
CATEGORIES[Added]=""
CATEGORIES[Fixed]=""
CATEGORIES[Changed]=""
CATEGORIES[Removed]=""

COMMIT_COUNT=0

while IFS='|' read -r hash subject author; do
  [[ -z "$hash" ]] && continue

  category=$(categorize_commit "$subject")
  # Format: - Subject (hash)
  short_hash="${hash:0:7}"
  if [[ -n "$REPO_URL" ]]; then
    entry="- ${subject} ([${short_hash}](${REPO_URL}/commit/${hash}))"
  else
    entry="- ${subject} (${short_hash})"
  fi

  CATEGORIES[$category]="${CATEGORIES[$category]}${entry}\n"
  COMMIT_COUNT=$((COMMIT_COUNT + 1))
done < <(git log ${RANGE} --pretty=format:'%H|%s|%an' --no-merges 2>/dev/null)

# ──────────────────────────────────────────────────────────
# Generate CHANGELOG.md
# ──────────────────────────────────────────────────────────

{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project will be documented in this file."
  echo ""
  echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)."
  echo ""
  echo "## [${VERSION}] - ${DATE}"
  echo ""

  for category in "Added" "Fixed" "Changed" "Removed"; do
    if [[ -n "${CATEGORIES[$category]}" ]]; then
      echo "### ${category}"
      echo ""
      echo -e "${CATEGORIES[$category]}"
    fi
  done

  # Footer
  echo "---"
  echo ""
  echo "*Generated from ${COMMIT_COUNT} commits.*"
} > "$OUTPUT"

echo "Generated ${OUTPUT} with ${COMMIT_COUNT} commits in 4 categories."
echo "  Added:   $(echo -e "${CATEGORIES[Added]}" | grep -c '^\-' 2>/dev/null || echo 0)"
echo "  Fixed:   $(echo -e "${CATEGORIES[Fixed]}" | grep -c '^\-' 2>/dev/null || echo 0)"
echo "  Changed: $(echo -e "${CATEGORIES[Changed]}" | grep -c '^\-' 2>/dev/null || echo 0)"
echo "  Removed: $(echo -e "${CATEGORIES[Removed]}" | grep -c '^\-' 2>/dev/null || echo 0)"
