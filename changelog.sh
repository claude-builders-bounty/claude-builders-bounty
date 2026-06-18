#!/usr/bin/env bash
# ============================================================
# changelog.sh — Generate CHANGELOG.md from git history
# ============================================================
# Usage:
#   bash changelog.sh              # Generate CHANGELOG.md
#   bash changelog.sh --stdout     # Print to stdout only
#   bash changelog.sh --tag=v1.0.0 # Start from a specific tag
# ============================================================
set -euo pipefail

OUTPUT_FILE="CHANGELOG.md"
PRINT_STDOUT=false
SINCE_TAG=""

for arg in "$@"; do
  case "$arg" in
    --stdout) PRINT_STDOUT=true ;;
    --tag=*) SINCE_TAG="${arg#*=}" ;;
    --help|-h)
      echo "Usage: bash changelog.sh [--stdout] [--tag=v1.0.0]" ; exit 0 ;;
  esac
done

# Determine commit range
if [ -z "$SINCE_TAG" ]; then
  LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
  if [ -z "$LATEST_TAG" ]; then
    RANGE=""
  else
    SINCE_TAG="$LATEST_TAG"
    RANGE="$LATEST_TAG..HEAD"
  fi
else
  RANGE="$SINCE_TAG..HEAD"
fi

# Categorize function
categorize() {
  local msg="$1"
  if echo "$msg" | grep -qiE '^feat(\(.*\))?:|^add'; then echo "Added"
  elif echo "$msg" | grep -qiE '^fix(\(.*\))?:|^bug|^hotfix'; then echo "Fixed"
  elif echo "$msg" | grep -qiE '^chore|^refactor|^perf|^change|^update|^improve'; then echo "Changed"
  elif echo "$msg" | grep -qiE '^revert|^remove|^deprecate|^delete'; then echo "Removed"
  else echo "Other"
  fi
}

# Fetch commits
if [ -z "${RANGE:-}" ]; then
  COMMITS=$(git log --oneline --no-merges HEAD 2>/dev/null || true)
else
  COMMITS=$(git log --oneline --no-merges "$RANGE" 2>/dev/null || true)
fi

if [ -z "$COMMITS" ]; then
  echo "# No commits found" >&2
  exit 0
fi

ADDED=""; FIXED=""; CHANGED=""; REMOVED=""; OTHER=""
COUNT=0

while IFS= read -r line; do
  [ -z "$line" ] && continue
  HASH=$(echo "$line" | cut -d' ' -f1)
  MSG=$(echo "$line" | cut -d' ' -f2-)
  CAT=$(categorize "$MSG")
  ENTRY="- $MSG ($HASH)\n"
  case "$CAT" in
    Added)    ADDED+="$ENTRY"; COUNT=$((COUNT+1)) ;;
    Fixed)    FIXED+="$ENTRY"; COUNT=$((COUNT+1)) ;;
    Changed)  CHANGED+="$ENTRY"; COUNT=$((COUNT+1)) ;;
    Removed)  REMOVED+="$ENTRY"; COUNT=$((COUNT+1)) ;;
    *)        OTHER+="$ENTRY"; COUNT=$((COUNT+1)) ;;
  esac
done <<< "$COMMITS"

# Generate
VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.0")
DATE=$(date +%Y-%m-%d)
OUTPUT="# Changelog\n\n## [$VERSION] — $DATE\n\n_${COUNT} commits since ${SINCE_TAG:-the beginning}_\n\n"

if [ -n "$ADDED" ]; then   OUTPUT+="### 🚀 Added\n\n$ADDED\n"; fi
if [ -n "$FIXED" ]; then   OUTPUT+="### 🐛 Fixed\n\n$FIXED\n"; fi
if [ -n "$CHANGED" ]; then OUTPUT+="### 🔄 Changed\n\n$CHANGED\n"; fi
if [ -n "$REMOVED" ]; then OUTPUT+="### 🗑️ Removed\n\n$REMOVED\n"; fi
if [ -n "$OTHER" ]; then   OUTPUT+="### 📋 Other\n\n$OTHER\n"; fi

if [ "$PRINT_STDOUT" = true ]; then
  echo -e "$OUTPUT"
else
  echo -e "$OUTPUT" > "$OUTPUT_FILE"
  echo "✓ $OUTPUT_FILE generated ($COUNT commits)" >&2
fi
