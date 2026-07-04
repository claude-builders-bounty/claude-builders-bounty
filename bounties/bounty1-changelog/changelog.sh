#!/usr/bin/env bash
# changelog.sh — Auto-generate CHANGELOG.md from git history
# Usage: bash changelog.sh [--output CHANGELOG.md] [--repo /path/to/repo]
set -euo pipefail

OUTPUT="CHANGELOG.md"
REPO_DIR="."
SINCE_TAG=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --output) OUTPUT="$2"; shift 2 ;;
    --repo) REPO_DIR="$2"; shift 2 ;;
    --since) SINCE_TAG="$2"; shift 2 ;;
    *) echo "Unknown: $1"; exit 1 ;;
  esac
done

cd "$REPO_DIR"

# Validate we're in a git repo
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: '$REPO_DIR' is not a git repository."
  exit 1
fi

# Determine the tag range
if [[ -z "$SINCE_TAG" ]]; then
  LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
  if [[ -n "$LAST_TAG" ]]; then
    SINCE_TAG="$LAST_TAG"
    RANGE="${SINCE_TAG}..HEAD"
  else
    RANGE="HEAD"
  fi
else
  RANGE="${SINCE_TAG}..HEAD"
fi

echo "Generating CHANGELOG from range: $RANGE"

# Get repo name
REPO_NAME=$(basename "$(git rev-parse --show-toplevel)" 2>/dev/null || echo "project")
VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "unreleased")
DATE=$(date +%Y-%m-%d)

cat > "$OUTPUT" << HEADER
# Changelog

## [${VERSION}] - ${DATE}

HEADER

# Categorize commits using conventional commit prefixes
categorize() {
  local prefix="$1"
  local emoji="$2"
  local category="$3"
  local pattern="$4"

  local commits
  if [[ -n "$SINCE_TAG" ]]; then
    commits=$(git log "${RANGE}" --grep="${pattern}" --format="%s" --reverse 2>/dev/null || true)
  else
    commits=$(git log "${RANGE}" --grep="${pattern}" --format="%s" --reverse 2>/dev/null || true)
  fi

  if [[ -n "$commits" ]]; then
    {
      echo "### ${emoji} ${category}"
      echo "$commits" | while IFS= read -r line; do
        # Strip the prefix (e.g., "feat: " or "feat(core): ")
        local clean
        clean=$(echo "$line" | sed -E 's/^[a-z]+(\([^)]*\))?!?:[[:space:]]*//')
        echo "- ${clean}"
      done
      echo ""
    } >> "$OUTPUT"
  fi
}

# Run categorizations
categorize "feat" "✨" "Added" "^feat"
categorize "fix" "🐛" "Fixed" "^fix"
categorize "refactor" "♻️" "Changed" "^refactor|^perf"
categorize "docs" "📝" "Documentation" "^docs"
categorize "style" "💄" "Styling" "^style"
categorize "test" "🧪" "Testing" "^test"
categorize "chore" "🔧" "Maintenance" "^chore|^ci|^build"
categorize "revert" "⏪" "Removed" "^revert|^remove|^BREAKING"

# If no conventional commits found, just list all commits since tag
if ! grep -q "^###" "$OUTPUT" 2>/dev/null; then
  echo "### 📋 All Changes" >> "$OUTPUT"
  git log "${RANGE}" --format="- %s (%an)" --reverse >> "$OUTPUT" 2>/dev/null || true
  echo "" >> "$OUTPUT"
fi

echo "✅ CHANGELOG written to $(pwd)/${OUTPUT}"
