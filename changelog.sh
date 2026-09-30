#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--since TAG] [--repo PATH]
set -euo pipefail

# ─── Defaults ────────────────────────────────────────────────────────────────
SINCE=""
REPO="."
OUTPUT="CHANGELOG.md"
UNRELEASED="Unreleased"

# ─── Parse flags ─────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --since) SINCE="$2"; shift 2 ;;
    --repo)  REPO="$2";  shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    --help|-h)
      echo "Usage: bash changelog.sh [--since TAG] [--repo PATH] [--output FILE]"
      echo ""
      echo "Generate a structured CHANGELOG.md from a git repository's history."
      echo ""
      echo "Options:"
      echo "  --since TAG   Start from this tag (default: latest tag, or all commits)"
      echo "  --repo PATH   Path to git repository (default: current directory)"
      echo "  --output FILE Output file path (default: CHANGELOG.md)"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

cd "$REPO"

# Validate it's a git repo
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: $REPO is not a git repository" >&2
  exit 1
fi

# ─── Determine commit range ──────────────────────────────────────────────────
if [[ -n "$SINCE" ]]; then
  RANGE="${SINCE}..HEAD"
  VERSION="$SINCE"
elif git describe --tags --abbrev=0 2>/dev/null; then
  LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
  if git rev-parse "${LATEST_TAG}^" >/dev/null 2>&1; then
    RANGE="${LATEST_TAG}..HEAD"
    VERSION="$LATEST_TAG"
  else
    # Only one commit or no parent
    RANGE="HEAD"
    VERSION="$UNRELEASED"
  fi
else
  RANGE="HEAD"
  VERSION="$UNRELEASED"
fi

# ─── Categorize commits ──────────────────────────────────────────────────────
declare -A CATEGORIES
CATEGORIES[Added]=""
CATEGORIES[Fixed]=""
CATEGORIES[Changed]=""
CATEGORIES[Removed]=""
CATEGORIES[Deprecated]=""
CATEGORIES[Security]=""

while IFS=$'\t' read -r hash message; do
  # Strip conventional commit prefix
  lower_msg=$(echo "$message" | tr '[:upper:]' '[:lower:]')

  # Truncated short hash
  short_hash="${hash:0:7}"

  if [[ "$lower_msg" =~ ^feat(\(.*\))?!?: ]]; then
    CATEGORIES[Added]+="  - ${message#*: } (#${short_hash})"$'\n'
  elif [[ "$lower_msg" =~ ^fix(\(.*\))?!?: ]]; then
    CATEGORIES[Fixed]+="  - ${message#*: } (#${short_hash})"$'\n'
  elif [[ "$lower_msg" =~ ^chore(\(.*\))?!?:|^refactor(\(.*\))?!?:|^perf(\(.*\))?!?: ]]; then
    CATEGORIES[Changed]+="  - ${message#*: } (#${short_hash})"$'\n'
  elif [[ "$lower_msg" =~ ^docs(\(.*\))?!?:|^style(\(.*\))?!?: ]]; then
    CATEGORIES[Changed]+="  - ${message#*: } (#${short_hash})"$'\n'
  elif [[ "$lower_msg" =~ ^revert(\(.*\))?!?:|^remove(\(.*\))?!?: ]]; then
    CATEGORIES[Removed]+="  - ${message#*: } (#${short_hash})"$'\n'
  elif [[ "$lower_msg" =~ ^security(\(.*\))?!?: ]]; then
    CATEGORIES[Security]+="  - ${message#*: } (#${short_hash})"$'\n'
  elif [[ "$lower_msg" =~ ^deprecat(\(.*\))?!?: ]]; then
    CATEGORIES[Deprecated]+="  - ${message#*: } (#${short_hash})"$'\n'
  else
    # Uncategorized — put in Changed
    CATEGORIES[Changed]+="  - $message (#${short_hash})"$'\n'
  fi
done < <(git log --format="%H%x09%s" "$RANGE" 2>/dev/null || echo "")

TOTAL_COMMITS=$(git rev-list --count "$RANGE" 2>/dev/null || echo "0")

# ─── Generate CHANGELOG.md ───────────────────────────────────────────────────
{
  echo "# Changelog"
  echo ""
  echo "## ${VERSION}"
  echo ""
  echo "_${TOTAL_COMMITS} commits_"
  echo ""

  for cat in Added Fixed Changed Removed Deprecated Security; do
    items="${CATEGORIES[$cat]}"
    if [[ -n "$items" ]]; then
      echo "### ${cat}"
      echo ""
      # Remove trailing blank line
      echo "$items" | sed '/^$/d'
      echo ""
    fi
  done

  if [[ "$VERSION" == "$UNRELEASED" ]]; then
    echo "---"
    echo "_No tags found. Generated from all available commits._"
    echo "_To target a specific release, use: bash changelog.sh --since v1.0.0_"
  fi
} > "$OUTPUT"

echo "✅ CHANGELOG.md generated with ${TOTAL_COMMITS} commits"
echo "   Output: $(pwd)/${OUTPUT}"
echo ""
echo "   Categories used:"
for cat in Added Fixed Changed Removed Deprecated Security; do
  items="${CATEGORIES[$cat]}"
  if [[ -n "$items" ]]; then
    count=$(echo "$items" | grep -c '^  -' || true)
    echo "     ${cat}: ${count}"
  fi
done