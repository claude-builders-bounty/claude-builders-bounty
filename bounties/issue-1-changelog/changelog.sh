#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--since <tag|commit>] [--output <file>]
# Requirements: git (any version)

set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
OUTPUT="CHANGELOG.md"
SINCE=""
VERSION=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --since)   SINCE="$2";  shift 2 ;;
    --output)  OUTPUT="$2"; shift 2 ;;
    --version) VERSION="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# ── Detect range ──────────────────────────────────────────────────────────────
if [[ -z "$SINCE" ]]; then
  # Use the most recent tag as baseline
  SINCE=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

if [[ -z "$SINCE" ]]; then
  echo "ℹ️  No tags found — using full history"
  RANGE=""
else
  echo "📌 Generating CHANGELOG since: $SINCE"
  RANGE="${SINCE}..HEAD"
fi

# ── Auto-detect version ───────────────────────────────────────────────────────
if [[ -z "$VERSION" ]]; then
  # Try package.json, then Cargo.toml, then next tag, then date
  if [[ -f "package.json" ]]; then
    VERSION=$(node -e "try{console.log(require('./package.json').version)}catch(e){}" 2>/dev/null || echo "")
  fi
  if [[ -z "$VERSION" ]] && [[ -f "Cargo.toml" ]]; then
    VERSION=$(grep '^version' Cargo.toml | head -1 | sed 's/.*= *"//' | sed 's/"//' || echo "")
  fi
  if [[ -z "$VERSION" ]]; then
    VERSION=$(date +"%Y-%m-%d")
  fi
fi

DATE=$(date +"%Y-%m-%d")

# ── Fetch commits ─────────────────────────────────────────────────────────────
# Format: <hash>|<subject>|<author>
COMMITS=$(git log ${RANGE} --pretty=format:"%H|%s|%an" --no-merges 2>/dev/null || echo "")

if [[ -z "$COMMITS" ]]; then
  echo "⚠️  No commits found in range. Nothing to generate."
  exit 0
fi

# ── Categorize ────────────────────────────────────────────────────────────────
declare -a ADDED FIXED CHANGED REMOVED UNCATEGORIZED

while IFS='|' read -r hash subject author; do
  [[ -z "$subject" ]] && continue

  lower=$(echo "$subject" | tr '[:upper:]' '[:lower:]')
  entry="- ${subject} (${author})"

  if echo "$lower" | grep -qE '^(feat|add|new|implement|create|introduce)(\(.+\))?[!:]?'; then
    ADDED+=("$entry")
  elif echo "$lower" | grep -qE '^(fix|bug|patch|hotfix|correct|resolve)(\(.+\))?[!:]?'; then
    FIXED+=("$entry")
  elif echo "$lower" | grep -qE '^(refactor|perf|improve|update|upgrade|change|style|chore|docs|ci|build|test)(\(.+\))?[!:]?'; then
    CHANGED+=("$entry")
  elif echo "$lower" | grep -qE '^(remove|delete|drop|deprecate|revert)(\(.+\))?[!:]?'; then
    REMOVED+=("$entry")
  else
    UNCATEGORIZED+=("$entry")
  fi
done <<< "$COMMITS"

# ── Write CHANGELOG ───────────────────────────────────────────────────────────
TMP=$(mktemp)

echo "# Changelog" > "$TMP"
echo "" >> "$TMP"

# Prepend to existing CHANGELOG if it exists
EXISTING=""
if [[ -f "$OUTPUT" ]]; then
  # Skip the first "# Changelog" line to avoid duplication
  EXISTING=$(tail -n +2 "$OUTPUT")
fi

cat >> "$TMP" << HEADER
## [${VERSION}] — ${DATE}

HEADER

write_section() {
  local title="$1"
  shift
  local items=("$@")
  if [[ ${#items[@]} -gt 0 ]]; then
    echo "### $title" >> "$TMP"
    for item in "${items[@]}"; do
      echo "$item" >> "$TMP"
    done
    echo "" >> "$TMP"
  fi
}

write_section "Added"   "${ADDED[@]+"${ADDED[@]}"}"
write_section "Fixed"   "${FIXED[@]+"${FIXED[@]}"}"
write_section "Changed" "${CHANGED[@]+"${CHANGED[@]}"}"
write_section "Removed" "${REMOVED[@]+"${REMOVED[@]}"}"

if [[ ${#UNCATEGORIZED[@]} -gt 0 ]]; then
  write_section "Other" "${UNCATEGORIZED[@]}"
fi

# Append previous content
if [[ -n "$EXISTING" ]]; then
  echo "" >> "$TMP"
  echo "---" >> "$TMP"
  echo "$EXISTING" >> "$TMP"
fi

mv "$TMP" "$OUTPUT"

# ── Summary ───────────────────────────────────────────────────────────────────
TOTAL=$(echo "$COMMITS" | wc -l | tr -d ' ')
echo "✅ CHANGELOG.md generated (${TOTAL} commits)"
echo "   📂 Output: ${OUTPUT}"
echo "   📦 Version: ${VERSION}"
echo "   ➕ Added: ${#ADDED[@]}  🐛 Fixed: ${#FIXED[@]}  🔄 Changed: ${#CHANGED[@]}  ❌ Removed: ${#REMOVED[@]}"
