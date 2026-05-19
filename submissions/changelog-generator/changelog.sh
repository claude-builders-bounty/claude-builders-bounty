#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--repo /path/to/repo] [--from-tag v1.0.0] [--output CHANGELOG.md]
#
# Works as a standalone script or as a Claude Code skill via /generate-changelog

set -euo pipefail

# ── Defaults ─────────────────────────────────────────────────────────────────
REPO_DIR="."
FROM_TAG=""
OUTPUT_FILE="CHANGELOG.md"
REPO_URL=""

# ── Parse args ───────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)     REPO_DIR="$2"; shift 2 ;;
    --from-tag) FROM_TAG="$2"; shift 2 ;;
    --output)   OUTPUT_FILE="$2"; shift 2 ;;
    --repo-url) REPO_URL="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash changelog.sh [--repo /path/to/repo] [--from-tag v1.0.0] [--output CHANGELOG.md] [--repo-url https://github.com/owner/repo]"
      echo ""
      echo "Generates a structured CHANGELOG.md from git history."
      echo "Auto-categorizes commits into: Added, Fixed, Changed, Removed."
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

cd "$REPO_DIR"

# ── Ensure we're in a git repo ──────────────────────────────────────────────
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "Error: not a git repository" >&2; exit 1
fi

# ── Determine the range ─────────────────────────────────────────────────────
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

if [[ -n "$FROM_TAG" ]]; then
  RANGE="${FROM_TAG}..HEAD"
elif [[ -n "$LATEST_TAG" ]]; then
  RANGE="${LATEST_TAG}..HEAD"
else
  RANGE="HEAD"
fi

# ── Get version header ──────────────────────────────────────────────────────
if [[ -n "$LATEST_TAG" ]]; then
  VERSION="Unreleased (changes since ${LATEST_TAG})"
else
  VERSION="Unreleased (all commits)"
fi

# ── Fetch commits using null-byte delimiters for safe parsing ────────────────
if [[ "$RANGE" == "HEAD" ]]; then
  COMMIT_DATA=$(git log --pretty=format:"%h%x09%s%x09%an%x09%ad" --date=short)
else
  COMMIT_DATA=$(git log --pretty=format:"%h%x09%s%x09%an%x09%ad" --date=short "$RANGE")
fi

if [[ -z "$COMMIT_DATA" ]]; then
  echo "No commits found in range: $RANGE" >&2
  exit 0
fi

# ── Categorize commits ──────────────────────────────────────────────────────
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

while IFS=$'\t' read -r short_hash subject author date; do
  # Build link if repo URL provided
  if [[ -n "$REPO_URL" ]]; then
    LINK="[${short_hash}](${REPO_URL}/commit/${short_hash})"
  else
    LINK="${short_hash}"
  fi

  ENTRY="- ${subject} (${LINK}) — ${author}, ${date}"

  # Categorize by conventional commit prefix or keyword
  LOWER=$(echo "$subject" | tr '[:upper:]' '[:lower:]')

  if [[ "$LOWER" =~ ^(feat|add|create|introduce|implement|new\ ) ]] || [[ "$LOWER" =~ :\ *(add|new|create|implement|introduce|feat) ]]; then
    ADDED="${ADDED}${ENTRY}"$'\n'
  elif [[ "$LOWER" =~ ^(fix|bug|patch|repair|resolve|hotfix|revert) ]]; then
    FIXED="${FIXED}${ENTRY}"$'\n'
  elif [[ "$LOWER" =~ ^(remove|delete|drop|deprecate|eliminate|strip) ]]; then
    REMOVED="${REMOVED}${ENTRY}"$'\n'
  elif [[ "$LOWER" =~ ^(change|update|modify|refactor|rename|move|upgrade|downgrade|migrate|bump|improve|enhance|optimize|chore|docs|ci|build|style|test|perf) ]]; then
    CHANGED="${CHANGED}${ENTRY}"$'\n'
  else
    OTHER="${OTHER}${ENTRY}"$'\n'
  fi
done <<< "$COMMIT_DATA"

# ── Generate CHANGELOG.md ───────────────────────────────────────────────────
{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project will be documented in this file."
  echo ""
  echo "## ${VERSION}"
  echo ""

  if [[ -n "$ADDED" ]]; then
    echo "### Added"
    echo ""
    echo -n "$ADDED"
    echo ""
  fi

  if [[ -n "$FIXED" ]]; then
    echo "### Fixed"
    echo ""
    echo -n "$FIXED"
    echo ""
  fi

  if [[ -n "$CHANGED" ]]; then
    echo "### Changed"
    echo ""
    echo -n "$CHANGED"
    echo ""
  fi

  if [[ -n "$REMOVED" ]]; then
    echo "### Removed"
    echo ""
    echo -n "$REMOVED"
    echo ""
  fi

  if [[ -n "$OTHER" ]]; then
    echo "### Other"
    echo ""
    echo -n "$OTHER"
    echo ""
  fi

} > "$OUTPUT_FILE"

echo "✅ Generated ${OUTPUT_FILE} from ${RANGE}"
COMMIT_COUNT=$(echo "$COMMIT_DATA" | wc -l | xargs)
echo "   ${COMMIT_COUNT} commits categorized"
