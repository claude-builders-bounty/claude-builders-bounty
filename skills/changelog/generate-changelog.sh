#!/usr/bin/env bash
# generate-changelog.sh — Generates a structured CHANGELOG.md from git history
# Usage: bash generate-changelog.sh [--since TAG] [--output FILE]
set -euo pipefail

# --- Config ---
SINCE_TAG=""
OUTPUT_FILE="CHANGELOG.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --since) SINCE_TAG="$2"; shift 2 ;;
    --output) OUTPUT_FILE="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--since TAG] [--output FILE]"
      echo "  --since TAG    Generate changelog since this tag (default: last tag)"
      echo "  --output FILE  Output file (default: CHANGELOG.md)"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# --- Find the last tag if not specified ---
if [[ -z "$SINCE_TAG" ]]; then
  SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

# --- Get commits ---
if [[ -n "$SINCE_TAG" ]]; then
  RANGE="${SINCE_TAG}..HEAD"
  echo "Generating changelog since $SINCE_TAG..."
else
  RANGE="HEAD"
  echo "No tags found. Generating changelog from all commits..."
fi

# Get commits in format: hash|subject
COMMITS=$(git log "$RANGE" --pretty=format:"%h|%s" --no-merges 2>/dev/null || echo "")

if [[ -z "$COMMITS" ]]; then
  echo "No commits found."
  exit 0
fi

# --- Categorize commits ---
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

while IFS='|' read -r hash subject; do
  [[ -z "$subject" ]] && continue

  # Normalize subject to lowercase for matching
  lower_subject=$(echo "$subject" | tr '[:upper:]' '[:lower:]')

  # Categorize based on conventional commit prefixes
  if [[ "$lower_subject" =~ ^feat(\(.*\))?!?:\  ]] || [[ "$lower_subject" =~ ^add(\(.*\))?!?:\  ]] || [[ "$lower_subject" =~ ^new(\(.*\))?!?:\  ]]; then
    ADDED="${ADDED}- ${subject} (\`${hash}\`)\n"
  elif [[ "$lower_subject" =~ ^fix(\(.*\))?!?:\  ]] || [[ "$lower_subject" =~ ^bug(\(.*\))?!?:\  ]] || [[ "$lower_subject" =~ ^patch(\(.*\))?!?:\  ]]; then
    FIXED="${FIXED}- ${subject} (\`${hash}\`)\n"
  elif [[ "$lower_subject" =~ ^remove(\(.*\))?!?:\  ]] || [[ "$lower_subject" =~ ^delete(\(.*\))?!?:\  ]] || [[ "$lower_subject" =~ ^drop(\(.*\))?!?:\  ]]; then
    REMOVED="${REMOVED}- ${subject} (\`${hash}\`)\n"
  elif [[ "$lower_subject" =~ ^refactor(\(.*\))?!?:\  ]] || [[ "$lower_subject" =~ ^update(\(.*\))?!?:\  ]] || [[ "$lower_subject" =~ ^change(\(.*\))?!?:\  ]] || [[ "$lower_subject" =~ ^improve(\(.*\))?!?:\  ]] || [[ "$lower_subject" =~ ^perf(\(.*\))?!?:\  ]] || [[ "$lower_subject" =~ ^chore(\(.*\))?!?:\  ]]; then
    CHANGED="${CHANGED}- ${subject} (\`${hash}\`)\n"
  elif [[ "$lower_subject" =~ ^docs(\(.*\))?!?:\  ]] || [[ "$lower_subject" =~ ^style(\(.*\))?!?:\  ]] || [[ "$lower_subject" =~ ^test(\(.*\))?!?:\  ]] || [[ "$lower_subject" =~ ^ci(\(.*\))?!?:\  ]] || [[ "$lower_subject" =~ ^build(\(.*\))?!?:\  ]]; then
    CHANGED="${CHANGED}- ${subject} (\`${hash}\`)\n"
  else
    OTHER="${OTHER}- ${subject} (\`${hash}\`)\n"
  fi
done <<< "$COMMITS"

# --- Generate output ---
DATE=$(date +%Y-%m-%d)
{
  echo "# Changelog"
  echo ""
  if [[ -n "$SINCE_TAG" ]]; then
    echo "## [Unreleased] — ${DATE}"
  else
    echo "## [Initial] — ${DATE}"
  fi
  echo ""

  if [[ -n "$ADDED" ]]; then
    echo "### Added"
    echo -e "$ADDED"
  fi

  if [[ -n "$FIXED" ]]; then
    echo "### Fixed"
    echo -e "$FIXED"
  fi

  if [[ -n "$CHANGED" ]]; then
    echo "### Changed"
    echo -e "$CHANGED"
  fi

  if [[ -n "$REMOVED" ]]; then
    echo "### Removed"
    echo -e "$REMOVED"
  fi

  if [[ -n "$OTHER" ]]; then
    echo "### Other"
    echo -e "$OTHER"
  fi
} > "$OUTPUT_FILE"

echo "Changelog written to $OUTPUT_FILE"
echo "Categories: Added=$(echo -e "$ADDED" | grep -c '^-' || true), Fixed=$(echo -e "$FIXED" | grep -c '^-' || true), Changed=$(echo -e "$CHANGED" | grep -c '^-' || true), Removed=$(echo -e "$REMOVED" | grep -c '^-' || true)"
