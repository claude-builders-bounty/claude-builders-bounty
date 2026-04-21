#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [output_file]
#
# Features:
#   - Fetches commits since the last git tag (or all commits if no tags exist)
#   - Auto-categorizes into: Added / Fixed / Changed / Removed
#   - Outputs a properly formatted CHANGELOG.md
#
# Commit categorization rules (case-insensitive prefix matching):
#   Added:   feat, add, new, implement, introduce, create, support
#   Fixed:   fix, bugfix, patch, resolve, repair, correct, hotfix
#   Changed: refactor, update, change, modify, improve, enhance, perf, style, rename, move, migrate, adjust, optimize, upgrade, bump, ci, build, chore, docs, test
#   Removed: remove, delete, drop, deprecate, clean, strip, uninstall

set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"

# Ensure we're inside a git repository
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "Error: Not inside a git repository." >&2
  exit 1
fi

# Determine the range of commits to include
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)

if [[ -n "$LATEST_TAG" ]]; then
  RANGE="${LATEST_TAG}..HEAD"
  SINCE_LABEL="since tag \`${LATEST_TAG}\`"
else
  RANGE=""
  SINCE_LABEL="(all commits — no tags found)"
fi

# Collect commits (short hash + subject)
if [[ -n "$RANGE" ]]; then
  COMMITS=$(git log "$RANGE" --pretty=format:"%h %s" 2>/dev/null || true)
else
  COMMITS=$(git log --pretty=format:"%h %s" 2>/dev/null || true)
fi

if [[ -z "$COMMITS" ]]; then
  echo "No commits found ${SINCE_LABEL}."
  exit 0
fi

# Get current date
TODAY=$(date +%Y-%m-%d)

# Get repo name
REPO_NAME=$(basename "$(git rev-parse --show-toplevel)")

# Categorize commits
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
UNCATEGORIZED=()

while IFS= read -r line; do
  [[ -z "$line" ]] && continue

  hash="${line%% *}"
  subject="${line#* }"

  # Normalize: strip conventional commit scope, e.g. "feat(scope): msg" -> "feat: msg"
  normalized=$(echo "$subject" | sed -E 's/^([a-zA-Z]+)\([^)]*\)/\1/')
  # Extract the keyword (first word before colon or space)
  keyword=$(echo "$normalized" | sed -E 's/^([a-zA-Z]+)[: ].*/\1/' | tr '[:upper:]' '[:lower:]')

  entry="- ${subject} (\`${hash}\`)"

  case "$keyword" in
    feat|add|new|implement|introduce|create|support)
      ADDED+=("$entry")
      ;;
    fix|bugfix|patch|resolve|repair|correct|hotfix)
      FIXED+=("$entry")
      ;;
    refactor|update|change|modify|improve|enhance|perf|style|rename|move|migrate|adjust|optimize|upgrade|bump|ci|build|chore|docs|test)
      CHANGED+=("$entry")
      ;;
    remove|delete|drop|deprecate|clean|strip|uninstall)
      REMOVED+=("$entry")
      ;;
    *)
      UNCATEGORIZED+=("$entry")
      ;;
  esac
done <<< "$COMMITS"

# Build CHANGELOG content
{
  echo "# Changelog"
  echo ""
  echo "All notable changes to **${REPO_NAME}** will be documented in this file."
  echo ""
  echo "The format is based on [Keep a Changelog](https://keepachangelog.com/)."
  echo ""

  if [[ -n "$LATEST_TAG" ]]; then
    echo "## [Unreleased] ${SINCE_LABEL}"
  else
    echo "## [Unreleased] — ${TODAY}"
  fi
  echo ""

  if [[ ${#ADDED[@]} -gt 0 ]]; then
    echo "### Added"
    printf '%s\n' "${ADDED[@]}"
    echo ""
  fi

  if [[ ${#FIXED[@]} -gt 0 ]]; then
    echo "### Fixed"
    printf '%s\n' "${FIXED[@]}"
    echo ""
  fi

  if [[ ${#CHANGED[@]} -gt 0 ]]; then
    echo "### Changed"
    printf '%s\n' "${CHANGED[@]}"
    echo ""
  fi

  if [[ ${#REMOVED[@]} -gt 0 ]]; then
    echo "### Removed"
    printf '%s\n' "${REMOVED[@]}"
    echo ""
  fi

  if [[ ${#UNCATEGORIZED[@]} -gt 0 ]]; then
    echo "### Other"
    printf '%s\n' "${UNCATEGORIZED[@]}"
    echo ""
  fi

  echo "---"
  echo "*Generated on ${TODAY} by [changelog-generator](https://github.com/claude-builders-bounty/claude-builders-bounty/tree/main/skills/changelog-generator)*"
} > "$OUTPUT_FILE"

# Summary
TOTAL=$(( ${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} + ${#UNCATEGORIZED[@]} ))
echo "✅ Generated ${OUTPUT_FILE} with ${TOTAL} entries ${SINCE_LABEL}"
echo "   Added: ${#ADDED[@]} | Fixed: ${#FIXED[@]} | Changed: ${#CHANGED[@]} | Removed: ${#REMOVED[@]} | Other: ${#UNCATEGORIZED[@]}"
