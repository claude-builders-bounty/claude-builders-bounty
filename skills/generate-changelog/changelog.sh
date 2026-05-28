#!/usr/bin/env bash
# ============================================================
# changelog.sh — Generate structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--dry-run] [--since <tag>]
# ============================================================
set -euo pipefail

DRY_RUN=false
SINCE_TAG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --since) SINCE_TAG="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

# ── Find the reference point (last tag or first commit) ──
if [[ -n "$SINCE_TAG" ]]; then
  REF="$SINCE_TAG"
else
  REF=$(git describe --tags --abbrev=0 2>/dev/null || git tag --sort=-v:refname 2>/dev/null | head -1 || true)
fi

if [[ -z "$REF" ]]; then
  # No tags exist — use the first commit
  REF=$(git rev-list --max-parents=0 HEAD)
  echo "⚠ No git tags found. Using first commit as baseline."
fi

echo "📋 Generating changelog from $REF to HEAD..."

# ── Collect commits ──
COMMITS=$(git log "$REF"..HEAD --no-merges --pretty=format:"%s" 2>/dev/null || true)

if [[ -z "$COMMITS" ]]; then
  echo "⚠ No new commits since $REF."
  exit 0
fi

# ── Categorization heuristics ──
declare -A CATEGORIES
CATEGORIES["Added"]=""
CATEGORIES["Fixed"]=""
CATEGORIES["Changed"]=""
CATEGORIES["Removed"]=""

while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  msg=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

  # Classify by conventional commit prefix or keyword
  lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

  if echo "$lower" | grep -qE '^(feat[:\(]|add |create |new |implement)'; then
    CATEGORIES["Added"]+="  - $msg"$'\n'
  elif echo "$lower" | grep -qE '^(fix[:\(]|bug|resolve |patch |repair|correct)'; then
    CATEGORIES["Fixed"]+="  - $msg"$'\n'
  elif echo "$lower" | grep -qE '(remove |delete |drop |deprecat|obsolete)'; then
    CATEGORIES["Removed"]+="  - $msg"$'\n'
  elif echo "$lower" | grep -qE '^(refactor|update |change |improve|optimize|upgrade|enhance|tweak|adjust|rework|rewrite|clean|chore|style|perf|ci|test|docs|build)'; then
    CATEGORIES["Changed"]+="  - $msg"$'\n'
  else
    # Default: Changed
    CATEGORIES["Changed"]+="  - $msg"$'\n'
  fi
done <<< "$COMMITS"

# ── Determine version ──
NEXT_VERSION="${NEXT_VERSION:-}"
if [[ -z "$NEXT_VERSION" ]]; then
  if [[ "$REF" =~ ^v?([0-9]+\.[0-9]+\.[0-9]+) ]]; then
    CURRENT="${BASH_REMATCH[1]}"
    IFS='.' read -r major minor patch <<< "$CURRENT"
    NEXT_VERSION="${major}.${minor}.$((patch + 1))"
  else
    NEXT_VERSION="0.1.0"
  fi
fi

TODAY=$(date +%Y-%m-%d)

# ── Build output ──
OUTPUT=""
OUTPUT+="# Changelog"$'\n\n'
OUTPUT+="## [${NEXT_VERSION}] — ${TODAY}"$'\n\n'

for category in "Added" "Fixed" "Changed" "Removed"; do
  content="${CATEGORIES[$category]}"
  if [[ -n "$content" ]]; then
    OUTPUT+="### $category"$'\n'
    OUTPUT+="$content"$'\n'
  fi
done

# ── Output ──
if $DRY_RUN; then
  echo ""
  echo "$OUTPUT"
else
  OUT_FILE="CHANGELOG.md"
  if [[ -f "$OUT_FILE" ]]; then
    # Prepend to existing CHANGELOG
    EXISTING=$(cat "$OUT_FILE")
    echo "$OUTPUT"$'\n'"$EXISTING" > "$OUT_FILE"
    echo "✅ Prepended to existing $OUT_FILE"
  else
    echo "$OUTPUT" > "$OUT_FILE"
    echo "✅ Created $OUT_FILE"
  fi
fi
