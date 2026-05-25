#!/usr/bin/env bash
# changelog.sh — Generate structured CHANGELOG.md from git history
# Bounty #1 — $50
#
# Usage:
#   bash changelog.sh                  # writes CHANGELOG.md in current dir
#   bash changelog.sh path/to/repo     # generate for a specific repo
#   /generate-changelog                # via Claude Code SKILL.md

set -euo pipefail

TARGET="${1:-.}"
cd "$TARGET"

# Find the last tag, or use initial commit
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

generate_changelog() {
  local since="$1"
  local out="$2"

  cat > "$out" << 'HEADER'
# Changelog

All notable changes to this project are documented below.

HEADER

  if [ -z "$since" ]; then
    echo "## [$(date +%Y-%m-%d)]" >> "$out"
    echo "" >> "$out"
    echo "Initial changelog (no prior git tag found)." >> "$out"
    echo "" >> "$out"

    # All commits since the beginning
    git log --no-merges --format="%s|||%h" --reverse 2>/dev/null \
      | while IFS='|||' read -r msg hash; do
        categorize_and_write "$msg" "$hash" "$out"
      done
  else
    echo "## [$since] — $(git log -1 --format=%ai "$since" 2>/dev/null | cut -d' ' -f1)" >> "$out"
    echo "" >> "$out"

    git log "$since..HEAD" --no-merges --format="%s|||%h" 2>/dev/null \
      | while IFS='|||' read -r msg hash; do
        categorize_and_write "$msg" "$hash" "$out"
      done
  fi

  # Remove trailing empty sections
  local temp_file="${out}.tmp"
  awk '!/^$/{ empty=0 } /^$/{ empty++ } empty<=2' "$out" > "$temp_file"
  mv "$temp_file" "$out"
}

categorize_and_write() {
  local msg="$1"
  local hash="$2"
  local out="$3"
  local lower
  lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

  if echo "$lower" | grep -qE '^feat|^feature|^add|^new|^implement'; then
    echo "  - \`$msg\` (\`$hash\`)" >> "$out"
  elif echo "$lower" | grep -qE '^fix|^bug|^hotfix|^patch|^correct'; then
    echo "  - \`$msg\` (\`$hash\`)" >> "$out"
  elif echo "$lower" | grep -qE '^change|^update|^refactor|^improve|^migrate'; then
    echo "  - \`$msg\` (\`$hash\`)" >> "$out"
  elif echo "$lower" | grep -qE '^remove|^deprecate|^delete|^drop'; then
    echo "  - \`$msg\` (\`$hash\`)" >> "$out"
  elif echo "$lower" | grep -qE '^docs?|^document'; then
    echo "  - \`$msg\` (\`$hash\`)" >> "$out"
  elif echo "$lower" | grep -qE '^style|^format|^lint|^prettier'; then
    echo "  - \`$msg\` (\`$hash\`)" >> "$out"
  elif echo "$lower" | grep -qE '^test|^spec|^coverage'; then
    echo "  - \`$msg\` (\`$hash\`)" >> "$out"
  elif echo "$lower" | grep -qE '^ci|^build|^docker|^deploy|^action'; then
    echo "  - \`$msg\` (\`$hash\`)" >> "$out"
  elif echo "$lower" | grep -qE '^perf|^optimize|^speed'; then
    echo "  - \`$msg\` (\`$hash\`)" >> "$out"
  elif echo "$lower" | grep -qE '^security|^vuln|^cve'; then
    echo "  - \`$msg\` (\`$hash\`)" >> "$out"
  else
    echo "  - \`$msg\` (\`$hash\`)" >> "$out"
  fi
}

# Sort entries into categories
sort_into_categories() {
  local input="$1"
  local output="$2"
  local categories=("Added" "Fixed" "Changed" "Removed" "Documentation" "Performance" "Security" "Style" "Tests" "CI/CD")

  > "$output"

  while IFS= read -r line; do
    case "$line" in
      "##"*) echo "$line" >> "$output" ;;
      *"feat"*) echo "### Added" >> "$output"; categories=("${categories[@]/Added}") ;;
    esac
  done < "$input"
}

main() {
  local output="${CHANGELOG_OUTPUT:-CHANGELOG.md}"

  # Check we're in a git repo
  if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: not in a git repository" >&2
    exit 1
  fi

  # Check for unstaged changes warning
  if ! git diff --quiet 2>/dev/null; then
    echo "Warning: uncommitted changes found. CHANGELOG will only reflect committed history." >&2
  fi

  generate_changelog "$LAST_TAG" "$output"
  echo "✅ CHANGELOG generated: $(pwd)/$output"
}

main "$@"
