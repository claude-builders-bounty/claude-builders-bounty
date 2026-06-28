#!/usr/bin/env bash
# changelog.sh — Generate structured CHANGELOG.md from git history
# Usage: ./changelog.sh [--stdout] [--output FILE] [--since TAG]
# 
# Auto-categorizes commits by conventional commit type:
#   feat     → Added
#   fix      → Fixed
#   refactor/perf/build/docs/style/test/chore → Changed
#   remove/delete/deprecate → Removed

set -euo pipefail

OUTPUT="CHANGELOG.md"
STDOUT=false
SINCE_TAG=""

# Parse args
for arg in "$@"; do
  case "$arg" in
    --stdout)   STDOUT=true ;;
    --output=*) OUTPUT="${arg#--output=}" ;;
    --since=*)  SINCE_TAG="${arg#--since=}" ;;
    -h|--help)
      head -6 "$0" | tail -5 | sed 's/^# \?//'
      exit 0
      ;;
  esac
done

# Get the latest tag
if [ -z "$SINCE_TAG" ]; then
  SINCE_TAG=$(git tag --sort=-v:refname 2>/dev/null | head -1 || echo "")
fi

# Build commit range
if [ -n "$SINCE_TAG" ]; then
  RANGE="${SINCE_TAG}..HEAD"
  VERSION=$(git describe --tags --abbrev=0 2>/dev/null | sed 's/^v//' || echo "0.0.0")
  # Bump minor version
  MAJOR=$(echo "$VERSION" | cut -d. -f1)
  MINOR=$(echo "$VERSION" | cut -d. -f2)
  NEXT_MINOR=$((MINOR + 1))
  NEXT_VERSION="${MAJOR}.${NEXT_MINOR}.0"
else
  RANGE="HEAD"
  NEXT_VERSION="0.1.0"
fi

DATE=$(date +%Y-%m-%d)

# Collect commits by category
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r line; do
  msg=$(echo "$line" | sed 's/^[a-f0-9]* //')
  type=$(echo "$msg" | grep -oE '^[a-zA-Z]+' || echo "")
  
  case "$type" in
    feat|feature)
      ADDED="${ADDED}- ${msg}"$'\n'
      ;;
    fix|bugfix|hotfix)
      FIXED="${FIXED}- ${msg}"$'\n'
      ;;
    remove|delete|deprecate)
      REMOVED="${REMOVED}- ${msg}"$'\n'
      ;;
    *)
      CHANGED="${CHANGED}- ${msg}"$'\n'
      ;;
  esac
done < <(git log "$RANGE" --oneline --no-merges 2>/dev/null || git log --oneline --no-merges -20)

# Generate markdown
generate_changelog() {
  cat <<EOF
# Changelog

All notable changes to this project will be documented in this file.

## [${NEXT_VERSION}] — ${DATE}
EOF

  if [ -n "$ADDED" ]; then
    echo ""
    echo "### Added"
    echo "$ADDED" | sed '/^$/d'
  fi

  if [ -n "$FIXED" ]; then
    echo ""
    echo "### Fixed"
    echo "$FIXED" | sed '/^$/d'
  fi

  if [ -n "$CHANGED" ]; then
    echo ""
    echo "### Changed"
    echo "$CHANGED" | sed '/^$/d'
  fi

  if [ -n "$REMOVED" ]; then
    echo ""
    echo "### Removed"
    echo "$REMOVED" | sed '/^$/d'
  fi

  echo ""
}

# Output
if $STDOUT; then
  generate_changelog
else
  # Prepend to existing CHANGELOG.md if it exists
  if [ -f "$OUTPUT" ]; then
    TMP=$(mktemp)
    generate_changelog > "$TMP"
    # Skip the header lines from existing file (first 3 lines)
    tail -n +4 "$OUTPUT" >> "$TMP"
    mv "$TMP" "$OUTPUT"
  else
    generate_changelog > "$OUTPUT"
  fi
  echo "✅ CHANGELOG.md generated (${NEXT_VERSION})"
fi
