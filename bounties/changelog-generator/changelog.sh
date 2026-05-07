#!/usr/bin/env bash
# CHANGELOG Generator — auto-generate CHANGELOG.md from git history
# Usage: bash changelog.sh [--since TAG] [--repo PATH]
set -euo pipefail

REPO="${2:-.}"
SINCE_TAG=""
OUTPUT="CHANGELOG.md"

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --since) SINCE_TAG="$2"; shift 2 ;;
    --repo)  REPO="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    *) echo "Usage: $0 [--since TAG] [--repo PATH] [--output FILE]"; exit 1 ;;
  esac
done

cd "$REPO"

# Determine the revision range
if [[ -n "$SINCE_TAG" ]]; then
  RANGE="${SINCE_TAG}..HEAD"
elif [[ -n "$(git tag --sort=-creatordate 2>/dev/null | head -1)" ]]; then
  LATEST_TAG=$(git tag --sort=-creatordate | head -1)
  PREV_TAG=$(git tag --sort=-creatordate | sed -n '2p')
  if [[ -n "$PREV_TAG" ]]; then
    RANGE="${PREV_TAG}..HEAD"
  else
    RANGE=""
  fi
  echo "# Changelog since ${PREV_TAG:-$LATEST_TAG}" > "$OUTPUT"
else
  RANGE=""
  echo "# Changelog (full history)" > "$OUTPUT"
fi

echo "" >> "$OUTPUT"
echo "## [$(date +%Y-%m-%d)]" >> "$OUTPUT"
echo "" >> "$OUTPUT"

# Categorize commits
categorize() {
  local category="$1"
  local pattern="$2"
  local commits
  
  if [[ -n "$RANGE" ]]; then
    commits=$(git log "$RANGE" --grep="$pattern" --format="- %s (%h)" --reverse 2>/dev/null || true)
  else
    commits=$(git log --grep="$pattern" --format="- %s (%h)" --reverse 2>/dev/null || true)
  fi
  
  if [[ -n "$commits" ]]; then
    echo "### $category" >> "$OUTPUT"
    echo "$commits" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
  fi
}

categorize "🚀 Added" "^feat\|^add\|^feature\|^implement"
categorize "🔧 Fixed" "^fix\|^bugfix\|^hotfix\|^patch"
categorize "🔄 Changed" "^refactor\|^change\|^update\|^improve\|^perf"
categorize "🗑️ Removed" "^remove\|^delete\|^deprecat"
categorize "📝 Documentation" "^docs\|^doc\|^readme"
categorize "🧪 Testing" "^test\|^testing\|^spec"

# Unclassified commits
unclassified=$(if [[ -n "$RANGE" ]]; then git log "$RANGE" --format="- %s (%h)" --reverse 2>/dev/null; else git log --format="- %s (%h)" --reverse 2>/dev/null; fi | grep -v -E "^(feat|add|feature|implement|fix|bugfix|hotfix|patch|refactor|change|update|improve|perf|remove|delete|deprecat|docs|doc|readme|test|testing|spec)" || true)
if [[ -n "$unclassified" ]]; then
  echo "### 📦 Other" >> "$OUTPUT"
  echo "$unclassified" >> "$OUTPUT"
  echo "" >> "$OUTPUT"
fi

# Stats
if [[ -n "$RANGE" ]]; then
  total=$(git log "$RANGE" --oneline 2>/dev/null | wc -l)
  authors=$(git log "$RANGE" --format="%an" 2>/dev/null | sort -u | paste -sd, -)
  echo "---" >> "$OUTPUT"
  echo "_${total} commits by ${authors}_" >> "$OUTPUT"
fi

echo ""
echo "✅ CHANGELOG generated: $(pwd)/${OUTPUT}"
echo "   $(wc -l < "$OUTPUT") lines"
