#!/usr/bin/env bash
# =============================================================================
# generate-changelog.sh — Auto-generate structured CHANGELOG.md from git history
# =============================================================================
# Usage:
#   ./generate-changelog.sh                    # Generate from all history
#   ./generate-changelog.sh --since v1.0.0     # From a specific tag/version
#   ./generate-changelog.sh --output CHANGELOG.md  # Custom output path
#   ./generate-changelog.sh --dry-run          # Preview without writing
# =============================================================================

set -euo pipefail

# ── Defaults ────────────────────────────────────────────────────────────────
OUTPUT_FILE="CHANGELOG.md"
SINCE=""
DRY_RUN=false
PROJECT_NAME="$(basename "$(git rev-parse --show-toplevel)" 2>/dev/null || echo 'My Project')"
PROJECT_VERSION="$(git describe --tags --abbrev=0 2>/dev/null || echo 'Unreleased')"

# ── Parse arguments ─────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --since)
      SINCE="$2"
      shift 2
      ;;
    --output)
      OUTPUT_FILE="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --since TAG        Generate changelog since TAG (e.g., v1.0.0)"
      echo "  --output FILE      Output file (default: CHANGELOG.md)"
      echo "  --dry-run          Preview without writing"
      echo "  --help, -h         Show this help"
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

# ── Validate git repo ───────────────────────────────────────────────────────
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "Error: Not a git repository" >&2
  exit 1
fi

# ── Determine version range ─────────────────────────────────────────────────
if [[ -n "$SINCE" ]]; then
  RANGE="$SINCE..HEAD"
  SINCE_LABEL="Since $SINCE"
else
  RANGE="HEAD"
  SINCE_LABEL="All commits"
fi

# ── Collect commits ─────────────────────────────────────────────────────────
COMMITS=$(git log --no-merges --format="%H|%ai|%s" --reverse "$RANGE" 2>/dev/null || true)

if [[ -z "$COMMITS" ]]; then
  echo "No commits found in range: $RANGE"
  exit 0
fi

TOTAL_COMMITS=$(echo "$COMMITS" | wc -l)
echo "Processing $TOTAL_COMMITS commits ($SINCE_LABEL)..."

# ── Categorize commits ──────────────────────────────────────────────────────
declare -a arr_features=()
declare -a arr_fixes=()
declare -a arr_docs=()
declare -a arr_refactors=()
declare -a arr_breakings=()
declare -a arr_others=()

while IFS='|' read -r hash date subject; do
  subj_lower=$(echo "$subject" | tr '[:upper:]' '[:lower:]')

  # Detect breaking changes
  if echo "$subject" | grep -qiE '^(break|breaking|feat\(.*\):.*\!)'; then
    arr_breakings+=("**${subject}** (${hash:0:7})")
    continue
  fi

  # Categorize
  if echo "$subj_lower" | grep -qE '^(feat|feature|add|new|implement)'; then
    arr_features+=("**${subject}** (${hash:0:7})")
  elif echo "$subj_lower" | grep -qE '^(fix|bug|repair|resolve|patch)'; then
    arr_fixes+=("**${subject}** (${hash:0:7})")
  elif echo "$subj_lower" | grep -qE '^(docs?|doc|document|comment|readme)'; then
    arr_docs+=("**${subject}** (${hash:0:7})")
  elif echo "$subj_lower" | grep -qE '^(refactor|ref|restructure|reorganize)'; then
    arr_refactors+=("**${subject}** (${hash:0:7})")
  else
    arr_others+=("**${subject}** (${hash:0:7})")
  fi
done <<< "$COMMITS"

# ── Build output ────────────────────────────────────────────────────────────
TIMESTAMP=$(date -u +"%Y-%m-%d")
VERSION_NUM=$(echo "$PROJECT_VERSION" | sed 's/^v//')
if [[ "$VERSION_NUM" =~ ^[0-9]+$ ]]; then
  NEXT_VERSION="v$((VERSION_NUM + 1)).0.0"
elif [[ "$VERSION_NUM" =~ ^[0-9]+\.[0-9]+$ ]]; then
  MAJOR=$(echo "$VERSION_NUM" | cut -d. -f1)
  MINOR=$(echo "$VERSION_NUM" | cut -d. -f2)
  NEXT_VERSION="v${MAJOR}.$((MINOR + 1)).0"
else
  NEXT_VERSION="v1.0.0"
fi

{
  echo "# Changelog"
  echo ""
  echo "All notable changes to **${PROJECT_NAME}** are documented in this file."
  echo ""
  echo "The format is based on [Keep a Changelog](https://keepachangelog.com/),"
  echo "and this project adheres to [Semantic Versioning](https://semver.org/)."
  echo ""
  echo "---"
  echo ""
  echo "## [${NEXT_VERSION}] — ${TIMESTAMP}"
  echo ""
  echo "> Generated from ${TOTAL_COMMITS} commits (${SINCE_LABEL})"
  echo ""

  if [[ ${#arr_breakings[@]} -gt 0 ]]; then
    echo "### ⚠️ Breaking Changes"
    echo ""
    for item in "${arr_breakings[@]}"; do
      echo "- ${item}"
    done
    echo ""
  fi

  if [[ ${#arr_features[@]} -gt 0 ]]; then
    echo "### ✨ Added"
    echo ""
    for item in "${arr_features[@]}"; do
      echo "- ${item}"
    done
    echo ""
  fi

  if [[ ${#arr_fixes[@]} -gt 0 ]]; then
    echo "### 🐛 Fixed"
    echo ""
    for item in "${arr_fixes[@]}"; do
      echo "- ${item}"
    done
    echo ""
  fi

  if [[ ${#arr_refactors[@]} -gt 0 ]]; then
    echo "### ♻️ Refactored"
    echo ""
    for item in "${arr_refactors[@]}"; do
      echo "- ${item}"
    done
    echo ""
  fi

  if [[ ${#arr_docs[@]} -gt 0 ]]; then
    echo "### 📚 Documentation"
    echo ""
    for item in "${arr_docs[@]}"; do
      echo "- ${item}"
    done
    echo ""
  fi

  if [[ ${#arr_others[@]} -gt 0 ]]; then
    echo "### 🔧 Other"
    echo ""
    for item in "${arr_others[@]}"; do
      echo "- ${item}"
    done
    echo ""
  fi

  echo "---"
  echo ""
  echo "_This changelog was auto-generated by \`generate-changelog.sh\`._"
} > /tmp/changelog_generated_$$

# ── Write or preview ────────────────────────────────────────────────────────
if [[ "$DRY_RUN" == true ]]; then
  cat /tmp/changelog_generated_$$
  echo ""
  echo "=== DRY RUN — not writing to ${OUTPUT_FILE} ==="
  rm -f /tmp/changelog_generated_$$
  exit 0
fi

if [[ -f "$OUTPUT_FILE" ]]; then
  # Keep existing header, prepend new section
  {
    head -1 "$OUTPUT_FILE"
    echo ""
    cat /tmp/changelog_generated_$$
    # Skip the header line of the existing file for the rest
    tail -n +2 "$OUTPUT_FILE"
  } > "${OUTPUT_FILE}.tmp"
  mv "${OUTPUT_FILE}.tmp" "$OUTPUT_FILE"
else
  mv /tmp/changelog_generated_$$ "$OUTPUT_FILE"
fi

echo "✅ Changelog written to ${OUTPUT_FILE} ($TOTAL_COMMITS commits processed)"
