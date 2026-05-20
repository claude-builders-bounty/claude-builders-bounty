#!/usr/bin/env bash
# changelog.sh — Structured CHANGELOG.md generator from git history
# Usage: bash changelog.sh [--since <tag>] [--output <file>]

set -euo pipefail

OUTPUT="${PWD}/CHANGELOG.md"
SINCE=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --since) SINCE="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

# Auto-detect last tag if --since not provided
if [[ -z "$SINCE" ]]; then
  SINCE=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

# Build git log range
if [[ -n "$SINCE" ]]; then
  RANGE="${SINCE}..HEAD"
  echo "→ Generating changelog since tag: $SINCE"
else
  RANGE="HEAD"
  echo "→ No tags found — using all commits"
fi

# Collect commits
COMMITS=$(git log "$RANGE" --pretty=format:"%s" --no-merges 2>/dev/null || echo "")

if [[ -z "$COMMITS" ]]; then
  echo "⚠ No commits found in range: $RANGE"
  exit 0
fi

# Categorize commits
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  
  # Strip leading/trailing whitespace
  msg="${line#"${line%%[![:space:]]*}"}"
  msg="${msg%"${msg##*[![:space:]]}"}"
  
  # Categorize by conventional commit prefix
  if   [[ "$msg" =~ ^[[:space:]]*(feat|add)[\(:\)\(\)] ]]; then
    ADDED+="  - $msg"$'\n'
  elif [[ "$msg" =~ ^[[:space:]]*(fix|bug|hotfix)[\(:\)\(\)] ]]; then
    FIXED+="  - $msg"$'\n'
  elif [[ "$msg" =~ ^[[:space:]]*(remove|revert|drop)[\(:\)\(\)] ]]; then
    REMOVED+="  - $msg"$'\n'
  else
    CHANGED+="  - $msg"$'\n'
  fi
done <<< "$COMMITS"

# Build changelog
VERSION=$(date +"%Y.%m.%d")
cat > "$OUTPUT" << CHANGELOG
# Changelog

## [$VERSION] — $(date +"%Y-%m-%d")

### Added
${ADDED:-  - _(none)_}

### Fixed
${FIXED:-  - _(none)_}

### Changed
${CHANGED:-  - _(none)_}

### Removed
${REMOVED:-  - _(none)_}
CHANGELOG

COMMIT_COUNT=$(echo "$COMMITS" | wc -l)
echo "✅ CHANGELOG.md generated ($COMMIT_COUNT commits, since: ${SINCE:-beginning})"
echo "   → $OUTPUT"
