#!/usr/bin/env bash
# ============================================================================
# generate-changelog.sh — Generate CHANGELOG.md from git history
#
# Features:
#   - Parses conventional commits (feat:, fix:, docs:, chore:, refactor:, etc.)
#   - Groups by type (Added, Fixed, Changed, Removed, etc.)
#   - Detects breaking changes (! or BREAKING CHANGE trailer)
#   - Handles edge cases: no tags, first commit, merge commits, empty repos
#   - Outputs a structured CHANGELOG.md with version, date, and categories
#
# Usage:
#   bash changelog.sh [--repo PATH] [--tag TAG] [--since REF] [--until REF]
#                     [--output FILE] [--version VER] [--help]
# ============================================================================
set -euo pipefail

# ---- Defaults ----
REPO="."
SINCE_TAG=""
SINCE_REF=""
UNTIL_REF="HEAD"
OUTPUT="CHANGELOG.md"
VERSION=""
HELP=false

# ---- Parse Arguments ----
while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)    REPO="$2";    shift 2 ;;
    --tag)     SINCE_TAG="$2"; shift 2 ;;
    --since)   SINCE_REF="$2"; shift 2 ;;
    --until)   UNTIL_REF="$2"; shift 2 ;;
    --output)  OUTPUT="$2";  shift 2 ;;
    --version) VERSION="$2"; shift 2 ;;
    --help|-h) HELP=true;    shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if $HELP; then
  echo "Usage: $0 [--repo PATH] [--tag TAG] [--since REF] [--until REF] [--output FILE] [--version VER]"
  echo ""
  echo "Generate a structured CHANGELOG.md from git history."
  echo ""
  echo "Options:"
  echo "  --repo PATH      Path to git repository (default: .)"
  echo "  --tag TAG        Tag to start from (e.g. v1.0.0)"
  echo "  --since REF      Git ref to start from (default: last tag or first commit)"
  echo "  --until REF      Git ref to end at (default: HEAD)"
  echo "  --output FILE    Output file path (default: CHANGELOG.md)"
  echo "  --version VER    Version string for this release (default: Unreleased)"
  echo "  --help           Show this help message"
  exit 0
fi

# ---- Validate repository ----
if [[ ! -d "$REPO/.git" ]] && [[ ! -f "$REPO/.git" ]]; then
  echo "Error: '$REPO' is not a git repository" >&2
  exit 1
fi

cd "$REPO"

# ---- Determine the "since" reference ----
# Priority: --tag > --since > last tag > first commit
if [[ -n "$SINCE_TAG" ]]; then
  SINCE_REF="$SINCE_TAG"
elif [[ -z "$SINCE_REF" ]]; then
  # Try to find the last tag
  LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
  if [[ -n "$LAST_TAG" ]]; then
    SINCE_REF="$LAST_TAG"
  else
    # No tags — use the root/first commit (empty tree)
    SINCE_REF=$(git rev-list --max-parents=0 HEAD 2>/dev/null || echo "")
    if [[ -z "$SINCE_REF" ]]; then
      echo "Error: No commits found in repository" >&2
      exit 1
    fi
  fi
fi

# ---- Determine version string ----
if [[ -z "$VERSION" ]]; then
  if [[ -n "$SINCE_TAG" ]]; then
    VERSION="$SINCE_TAG"
  else
    VERSION="Unreleased"
  fi
fi

# ---- Gather commits ----
FIRST_COMMIT=$(git rev-list --max-parents=0 HEAD 2>/dev/null || true)
COMMITS=""

if [[ "$SINCE_REF" == "$FIRST_COMMIT" ]]; then
  # From first commit — include everything up to UNTIL_REF
  # Use --root to include the root commit itself
  COMMITS=$(git log "$UNTIL_REF" --reverse --format="%H" 2>/dev/null || true)
elif git merge-base --is-ancestor "$SINCE_REF" "$UNTIL_REF" 2>/dev/null; then
  # Standard range: SINCE_REF..UNTIL_REF (excludes SINCE_REF itself)
  COMMITS=$(git log "$SINCE_REF..$UNTIL_REF" --reverse --format="%H" 2>/dev/null || true)
else
  # SINCE_REF is not an ancestor — try it as a range anyway
  COMMITS=$(git log "$SINCE_REF..$UNTIL_REF" --reverse --format="%H" 2>/dev/null || true)
fi

if [[ -z "$COMMITS" ]]; then
  echo "Warning: No commits found between ${SINCE_REF} and ${UNTIL_REF}" >&2
fi

# ---- Categorization ----
# We process each commit individually for better accuracy
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()
declare -a DOCS=()
declare -a PERF=()
declare -a TESTING=()
declare -a DEPS=()
declare -a OTHER=()
declare -a BREAKING=()

while IFS= read -r HASH; do
  [[ -z "$HASH" ]] && continue

  # Get the first line of the commit message (subject)
  SUBJECT=$(git log -1 --format="%s" "$HASH" 2>/dev/null || true)

  # Get the full body for BREAKING CHANGE detection
  BODY=$(git log -1 --format="%b" "$HASH" 2>/dev/null || true)

  # Check for merge commits
  PARENTS=$(git rev-list --parents -1 "$HASH" 2>/dev/null | awk '{print NF}')
  IS_MERGE=false
  if [[ "$PARENTS" -ge 3 ]]; then
    IS_MERGE=true
  fi

  # Check for breaking changes
  HAS_BREAKING=false
  if echo "$SUBJECT" | grep -qE '!\s*:' 2>/dev/null; then
    HAS_BREAKING=true
  fi
  if echo "$BODY" | grep -qi 'BREAKING CHANGE' 2>/dev/null; then
    HAS_BREAKING=true
  fi

  # Extract the commit description (strip prefix)
  DESCRIPTION=$(echo "$SUBJECT" | sed -E 's/^[a-z]+(\([^)]*\))?!?:\s*//' 2>/dev/null)
  if [[ -z "$DESCRIPTION" ]]; then
    DESCRIPTION="$SUBJECT"
  fi

  # Short hash
  SHORT_HASH=$(echo "$HASH" | cut -c1-7)

  # Format the entry
  ENTRY="$DESCRIPTION ([$SHORT_HASH](https://github.com/$(git config --get remote.origin.url 2>/dev/null | sed -E 's/.*[\/:]([^\/]+\/[^\/]+)\.git$/\1/')/commit/$HASH))"

  # If it's a breaking change, add to breaking list
  if $HAS_BREAKING; then
    BREAKING+=("$ENTRY")
  fi

  # Categorize by conventional commit type
  if echo "$SUBJECT" | grep -qE '^feat(\(' 2>/dev/null || echo "$SUBJECT" | grep -qE '^feat:'; then
    ADDED+=("$ENTRY")
  elif echo "$SUBJECT" | grep -qE '^fix(\(' 2>/dev/null || echo "$SUBJECT" | grep -qE '^fix:'; then
    FIXED+=("$ENTRY")
  elif echo "$SUBJECT" | grep -qE '^docs(\(' 2>/dev/null || echo "$SUBJECT" | grep -qE '^docs:'; then
    DOCS+=("$ENTRY")
  elif echo "$SUBJECT" | grep -qE '^perf(\(' 2>/dev/null || echo "$SUBJECT" | grep -qE '^perf:'; then
    PERF+=("$ENTRY")
  elif echo "$SUBJECT" | grep -qE '^test(\(' 2>/dev/null || echo "$SUBJECT" | grep -qE '^test:'; then
    TESTING+=("$ENTRY")
  elif echo "$SUBJECT" | grep -qE '^build(\(' 2>/dev/null || echo "$SUBJECT" | grep -qE '^(build|ci):'; then
    DEPS+=("$ENTRY")
  elif echo "$SUBJECT" | grep -qE '^(refactor|style|chore|revert)(\(' 2>/dev/null || \
       echo "$SUBJECT" | grep -qE '^(refactor|style|chore|revert):'; then
    CHANGED+=("$ENTRY")
  elif echo "$SUBJECT" | grep -qE '^remove(\(' 2>/dev/null || echo "$SUBJECT" | grep -qE '^(remove|deprecate|delete|drop):'; then
    REMOVED+=("$ENTRY")
  elif ! $IS_MERGE; then
    # Uncategorized non-merge commit
    OTHER+=("$ENTRY")
  fi
done <<< "$COMMITS"

# ---- Generate CHANGELOG.md ----
{
  echo "# Changelog"
  echo ""

  # Version header
  TODAY=$(date +%Y-%m-%d)
  echo "## [$VERSION] — $TODAY"
  echo ""

  # Breaking Changes (shown first, prominently)
  if [[ ${#BREAKING[@]} -gt 0 ]]; then
    echo "### ⚠ Breaking Changes"
    echo ""
    for entry in "${BREAKING[@]}"; do
      echo "- $entry"
    done
    echo ""
  fi

  # Added
  if [[ ${#ADDED[@]} -gt 0 ]]; then
    echo "### ✨ Added"
    echo ""
    for entry in "${ADDED[@]}"; do
      echo "- $entry"
    done
    echo ""
  fi

  # Fixed
  if [[ ${#FIXED[@]} -gt 0 ]]; then
    echo "### 🐛 Fixed"
    echo ""
    for entry in "${FIXED[@]}"; do
      echo "- $entry"
    done
    echo ""
  fi

  # Performance
  if [[ ${#PERF[@]} -gt 0 ]]; then
    echo "### ⚡ Performance"
    echo ""
    for entry in "${PERF[@]}"; do
      echo "- $entry"
    done
    echo ""
  fi

  # Changed
  if [[ ${#CHANGED[@]} -gt 0 ]]; then
    echo "### 🔄 Changed"
    echo ""
    for entry in "${CHANGED[@]}"; do
      echo "- $entry"
    done
    echo ""
  fi

  # Removed
  if [[ ${#REMOVED[@]} -gt 0 ]]; then
    echo "### 🗑 Removed"
    echo ""
    for entry in "${REMOVED[@]}"; do
      echo "- $entry"
    done
    echo ""
  fi

  # Documentation
  if [[ ${#DOCS[@]} -gt 0 ]]; then
    echo "### 📖 Documentation"
    echo ""
    for entry in "${DOCS[@]}"; do
      echo "- $entry"
    done
    echo ""
  fi

  # Testing
  if [[ ${#TESTING[@]} -gt 0 ]]; then
    echo "### 🧪 Testing"
    echo ""
    for entry in "${TESTING[@]}"; do
      echo "- $entry"
    done
    echo ""
  fi

  # Dependencies / Build
  if [[ ${#DEPS[@]} -gt 0 ]]; then
    echo "### 📦 Dependencies & Build"
    echo ""
    for entry in "${DEPS[@]}"; do
      echo "- $entry"
    done
    echo ""
  fi

  # Other
  if [[ ${#OTHER[@]} -gt 0 ]]; then
    echo "### 📝 Other"
    echo ""
    for entry in "${OTHER[@]}"; do
      echo "- $entry"
    done
    echo ""
  fi

  # Footer
  echo "---"
  echo "_Generated by [generate-changelog](skills/generate-changelog/changelog.sh) from ${SINCE_REF} to ${UNTIL_REF}_"
} > "$OUTPUT"

echo "✅ CHANGELOG.md generated — $(wc -l < "$OUTPUT") lines written to $OUTPUT"
