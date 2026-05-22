#!/usr/bin/env bash
# generate-changelog.sh — Auto-generate structured CHANGELOG.md from git history
# Usage: ./generate-changelog.sh [--tag TAG] [--output CHANGELOG.md] [--since TAG]
# Requires: git, bash 4+

set -euo pipefail

# ─── Config ──────────────────────────────────────────────────────────────────
OUTPUT="CHANGELOG.md"
SINCE_TAG=""
HEAD_TAG=""
GIT_DIR=$(git rev-parse --show-toplevel 2>/dev/null || echo ".")

# ─── Parse args ──────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case $1 in
    --output)   OUTPUT="$2";  shift 2 ;;
    --since)    SINCE_TAG="$2"; shift 2 ;;
    --tag)      HEAD_TAG="$2"; shift 2 ;;
    --help|-h)  echo "Usage: $0 [--tag TAG] [--output FILE] [--since TAG]"; exit 0 ;;
    *)          echo "Unknown option: $1"; exit 1 ;;
  esac
done

cd "$GIT_DIR"

# ─── Detect version ──────────────────────────────────────────────────────────
if [[ -z "$HEAD_TAG" ]]; then
  HEAD_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.0")
fi

DATE=$(date +"%Y-%m-%d")

# ─── Gather commits ──────────────────────────────────────────────────────────
if [[ -n "$SINCE_TAG" ]]; then
  RANGE="${SINCE_TAG}..HEAD"
else
  # If we have a previous tag, use it. Otherwise use initial commit.
  PREV_TAG=$(git tag --sort=-version:refname | head -2 | tail -1 2>/dev/null || echo "")
  if [[ -n "$PREV_TAG" ]]; then
    RANGE="${PREV_TAG}..HEAD"
  else
    RANGE="HEAD"
  fi
fi

# ─── Categorize commits by conventional commit type ──────────────────────────
declare -A SECTIONS
SECTIONS=(
  ["feat"]="🚀 Features"
  ["fix"]="🐛 Bug Fixes"
  ["docs"]="📝 Documentation"
  ["refactor"]="♻️ Refactoring"
  ["perf"]="⚡ Performance"
  ["test"]="🧪 Tests"
  ["ci"]="👷 CI/CD"
  ["chore"]="🔧 Chores"
  ["style"]="💄 Styling"
  ["revert"]="⏪ Reverts"
)

# Ordered list of section headings (what order they appear in the output)
SECTION_ORDER=("🚀 Features" "🐛 Bug Fixes" "⚡ Performance" "♻️ Refactoring" "📝 Documentation" "🧪 Tests" "👷 CI/CD" "💄 Styling" "🔧 Chores" "⏪ Reverts")

# Temporary files per section
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

for section in "${SECTION_ORDER[@]}"; do
  : > "$TMPDIR/$(echo "$section" | md5sum | cut -d' ' -f1)"
done

# Parse conventional commits
git log --oneline "$RANGE" --pretty=format:"%s" 2>/dev/null | while IFS= read -r line; do
  # Skip merge commits, version bumps, and dependency updates
  [[ "$line" =~ ^Merge\ pull\ request ]] && continue
  [[ "$line" =~ ^chore\(release\) ]] && continue
  [[ "$line" =~ ^chore\(deps\) ]] && continue

  # Extract type(scope): message
  if [[ "$line" =~ ^([a-z]+)(\([^)]+\))?:\ (.*) ]]; then
    TYPE="${BASH_REMATCH[1]}"
    SCOPE="${BASH_REMATCH[2]}"
    MESSAGE="${BASH_REMATCH[3]}"
    SCOPE_DISPLAY="${SCOPE//[()]/}"

    SECTION_KEY="${SECTIONS[$TYPE]:-}"
    if [[ -n "$SECTION_KEY" ]]; then
      HASH=$(echo "$SECTION_KEY" | md5sum | cut -d' ' -f1)
      if [[ -n "$SCOPE_DISPLAY" ]]; then
        echo "  - **$SCOPE_DISPLAY:** $MESSAGE" >> "$TMPDIR/$HASH"
      else
        echo "  - $MESSAGE" >> "$TMPDIR/$HASH"
      fi
    else
      # Uncategorized — put in "Other"
      HASH=$(echo "🔧 Chores" | md5sum | cut -d' ' -f1)
      echo "  - $line" >> "$TMPDIR/$HASH"
    fi
  fi
done

# ─── Generate CHANGELOG ──────────────────────────────────────────────────────
{
  echo "# Changelog"
  echo ""
  echo "## [$HEAD_TAG] - $DATE"
  echo ""

  HAS_CONTENT=false
  for section in "${SECTION_ORDER[@]}"; do
    HASH=$(echo "$section" | md5sum | cut -d' ' -f1)
    if [[ -s "$TMPDIR/$HASH" ]]; then
      echo "### $section"
      cat "$TMPDIR/$HASH"
      echo ""
      HAS_CONTENT=true
    fi
  done

  if [[ "$HAS_CONTENT" == false ]]; then
    echo "_No significant changes._"
    echo ""
  fi

  # Compare link
  if [[ -n "${PREV_TAG:-}" ]]; then
    echo "---"
    echo ""
    echo "**Full Changelog:** [$PREV_TAG...$HEAD_TAG](https://github.com/$(git remote get-url origin 2>/dev/null | sed 's|.*github.com[:/]||; s|\.git$||' 2>/dev/null || echo 'owner/repo')/compare/$PREV_TAG...$HEAD_TAG)"
  fi
} > "$OUTPUT"

echo "✅ Generated: $OUTPUT ($(wc -l < "$OUTPUT") lines)"