#!/usr/bin/env bash
# ============================================================================
# changelog.sh — Automated Structured CHANGELOG.md Generator from Git History
# Solves Issue #1: [BOUNTY $50] SKILL: Generate a structured CHANGELOG
# ============================================================================
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
REPO_PATH="${2:-.}"

cd "$REPO_PATH"

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -n "$LAST_TAG" ]; then
  RANGE="${LAST_TAG}..HEAD"
  HEADER_RANGE="Since tag \`${LAST_TAG}\`"
else
  RANGE="HEAD"
  HEADER_RANGE="All repository commits"
fi

DATE_STR=$(date -u +"%Y-%m-%d")

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS="|" read -r hash subject author date_short; do
  [ -z "$hash" ] && continue
  lower_subj=$(echo "$subject" | tr '[:upper:]' '[:lower:]')
  entry="- ${subject} (\`${hash}\` by ${author}, ${date_short})"

  if [[ "$lower_subj" =~ ^(feat|add|new|create|init|implement|spawn) ]] || [[ "$lower_subj" == *"add "* ]] || [[ "$lower_subj" == *"new "* ]]; then
    ADDED="${ADDED}${entry}\n"
  elif [[ "$lower_subj" =~ ^(fix|bug|hotfix|patch|resolve|repair) ]] || [[ "$lower_subj" == *"fix"* ]]; then
    FIXED="${FIXED}${entry}\n"
  elif [[ "$lower_subj" =~ ^(remove|delete|drop|clean|deprecate|cull) ]] || [[ "$lower_subj" == *"remove"* ]] || [[ "$lower_subj" == *"delete"* ]]; then
    REMOVED="${REMOVED}${entry}\n"
  else
    CHANGED="${CHANGED}${entry}\n"
  fi
done < <(git log "$RANGE" --pretty=format:"%h|%s|%an|%ad" --date=short)

{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project are automatically documented in this file."
  echo ""
  echo "## [Unreleased / ${DATE_STR}] — ${HEADER_RANGE}"
  echo ""
  echo "### Added"
  if [ -n "$ADDED" ]; then printf "%b" "$ADDED"; else echo "- _No new additions in this range._"; fi
  echo ""
  echo "### Fixed"
  if [ -n "$FIXED" ]; then printf "%b" "$FIXED"; else echo "- _No bug fixes in this range._"; fi
  echo ""
  echo "### Changed"
  if [ -n "$CHANGED" ]; then printf "%b" "$CHANGED"; else echo "- _No general changes in this range._"; fi
  echo ""
  echo "### Removed"
  if [ -n "$REMOVED" ]; then printf "%b" "$REMOVED"; else echo "- _No removals in this range._"; fi
} > "$OUTPUT_FILE"

echo "✅ Generated structured changelog at: ${OUTPUT_FILE} (${HEADER_RANGE})"
