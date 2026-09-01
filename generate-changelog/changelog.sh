#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Bounty: claude-builders-bounty #1 ($50)
# Stack: Bash (no dependencies beyond git + awk)
# Usage: bash changelog.sh [--from <tag>] [--to <ref>] [--output <file>] [--repo <path>]
set -euo pipefail

# ─── Defaults ───────────────────────────────────────────────────────────
FROM_TAG=""
TO_REF="HEAD"
OUTPUT_FILE="CHANGELOG.md"
REPO_PATH="."
# ────────────────────────────────────────────────────────────────────────

usage() {
  cat <<'EOF'
Usage: bash changelog.sh [OPTIONS]

Options:
  --from <tag>      Start from this git tag (default: last reachable tag)
  --to <ref>        End at this ref (default: HEAD)
  --output <file>   Output file path (default: CHANGELOG.md)
  --repo <path>     Path to git repository (default: current directory)
  -h, --help         Show this help message

Examples:
  bash changelog.sh
  bash changelog.sh --from v1.0.0 --to v2.0.0
  bash changelog.sh --output docs/CHANGELOG.md
EOF
}

# ─── Parse arguments ────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --from)   FROM_TAG="$2"; shift 2 ;;
    --to)     TO_REF="$2"; shift 2 ;;
    --output) OUTPUT_FILE="$2"; shift 2 ;;
    --repo)   REPO_PATH="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

# ─── Resolve git directory ──────────────────────────────────────────────
GIT_DIR="$REPO_PATH"
if ! git -C "$GIT_DIR" rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: '$GIT_DIR' is not a git repository." >&2
  exit 1
fi

# ─── Determine the start ref ────────────────────────────────────────────
if [[ -z "$FROM_TAG" ]]; then
  # Find the most recent tag reachable from TO_REF
  FROM_TAG=$(git -C "$GIT_DIR" describe --tags --abbrev=0 "$TO_REF" 2>/dev/null || true)
  # If FROM_TAG resolves to the same commit as TO_REF, find the previous tag
  if [[ -n "$FROM_TAG" ]]; then
    FROM_TAG_HASH=$(git -C "$GIT_DIR" rev-parse "$FROM_TAG" 2>/dev/null || true)
    TO_REF_HASH=$(git -C "$GIT_DIR" rev-parse "$TO_REF" 2>/dev/null || true)
    if [[ "$FROM_TAG_HASH" == "$TO_REF_HASH" ]]; then
      # HEAD is at a tag — find the tag before it
      PREV_TAG=$(git -C "$GIT_DIR" describe --tags --abbrev=0 "${FROM_TAG}^" 2>/dev/null || true)
      if [[ -n "$PREV_TAG" ]]; then
        FROM_TAG="$PREV_TAG"
      else
        # No previous tag — use all commits from the beginning
        FROM_TAG=""
      fi
    fi
  fi
fi

LATEST_TAG=""

if [[ -n "$FROM_TAG" ]]; then
  RANGE="${FROM_TAG}..${TO_REF}"
  LATEST_TAG="$FROM_TAG"
  VERSION="$TO_REF"
  # If TO_REF is HEAD, try to get a nicer version label
  if [[ "$TO_REF" == "HEAD" ]]; then
    COMMIT_COUNT=$(git -C "$GIT_DIR" rev-list --count "${FROM_TAG}..HEAD" 2>/dev/null || echo "0")
    if [[ "$COMMIT_COUNT" -eq 0 ]]; then
      VERSION="$FROM_TAG"
    else
      VERSION="${FROM_TAG} (${COMMIT_COUNT} commits since)"
    fi
  fi
else
  # No tags exist — use all commits
  RANGE=""
  VERSION="unreleased"
fi

# ─── Fetch commits ──────────────────────────────────────────────────────
if [[ -n "$RANGE" ]]; then
  COMMIT_LOG=$(git -C "$GIT_DIR" log "$RANGE" --no-merges --format="%H%x09%s%x09%an%x09%ad" --date=short 2>/dev/null || true)
else
  COMMIT_LOG=$(git -C "$GIT_DIR" log --no-merges --format="%H%x09%s%x09%an%x09%ad" --date=short 2>/dev/null || true)
fi

if [[ -z "$COMMIT_LOG" ]]; then
  echo "No commits found in the specified range." >&2
  exit 0
fi

# ─── Get date range ─────────────────────────────────────────────────────
# Prefer the tag creation date (more accurate for release notes);
# fall back to the most recent commit date in the range.
if [[ -n "$TO_REF" && "$TO_REF" != "HEAD" ]]; then
  # TO_REF is a tag — try to get the tag's creation date
  TAG_DATE=$(git -C "$GIT_DIR" for-each-ref --format='%(creatordate:short)' "refs/tags/${TO_REF}" 2>/dev/null | head -1)
  if [[ -n "$TAG_DATE" ]]; then
    DATE_RANGE="$TAG_DATE"
  fi
fi

if [[ -z "$DATE_RANGE" ]]; then
  if [[ -n "$RANGE" ]]; then
    DATE_RANGE=$(git -C "$GIT_DIR" log "$RANGE" --format="%ad" --date=short 2>/dev/null | sort -r | head -1)
  else
    DATE_RANGE=$(git -C "$GIT_DIR" log --format="%ad" --date=short 2>/dev/null | sort -r | head -1)
  fi
fi

# ─── Parse and categorize commits ───────────────────────────────────────
# Conventional commit format: type(scope)!: description
# We map types to categories:
#   feat        → Added
#   fix         → Fixed
#   refactor    → Changed
#   perf        → Changed
#   chore       → Changed
#   style       → Changed
#   build       → Changed
#   ci          → Changed
#   docs        → Changed
#   remove      → Removed
#   revert      → Removed
#   deprecate   → Removed
#   breaking    → Changed (with ⚠️ marker)

ADDED_ENTRIES=()
FIXED_ENTRIES=()
CHANGED_ENTRIES=()
REMOVED_ENTRIES=()

parse_commit_message() {
  local subject="$1"
  local author="$2"
  local date="$3"
  local hash="$4"

  # Extract conventional commit type
  local type="" scope="" desc="" breaking=""

  # Match: type(scope)!: description  OR  type!: description  OR  type: description
  # Store regex in a variable to avoid bash [[ ]] parsing issues
  local conv_regex='^([a-zA-Z]+)(\(([^)]+)\))?(!)?:[[:space:]]*(.+)$'
  if [[ "$subject" =~ $conv_regex ]]; then
    type="${BASH_REMATCH[1]}"
    scope="${BASH_REMATCH[3]}"
    breaking="${BASH_REMATCH[4]}"
    desc="${BASH_REMATCH[5]}"
  else
    # Non-conventional commit — put in Changed
    type="other"
    desc="$subject"
  fi

  # Lowercase type for matching
  local lower_type
  lower_type=$(echo "$type" | tr '[:upper:]' '[:lower:]')

  # Format the entry
  local entry
  if [[ -n "$scope" ]]; then
    entry="- **${scope}**: ${desc}"
  else
    entry="- ${desc}"
  fi

  # Add breaking change marker
  if [[ -n "$breaking" || "$lower_type" == "breaking" ]]; then
    entry="${entry} ⚠️ BREAKING"
  fi

  # Add author attribution
  entry="${entry} (${author})"

  # Categorize
  case "$lower_type" in
    feat|feature|add)
      ADDED_ENTRIES+=("$entry")
      ;;
    fix|bugfix|hotfix|patch)
      FIXED_ENTRIES+=("$entry")
      ;;
    refactor|perf|performance|chore|style|build|ci|docs|other|improve|update)
      CHANGED_ENTRIES+=("$entry")
      ;;
    remove|revert|deprecate|delete|drop)
      REMOVED_ENTRIES+=("$entry")
      ;;
    *)
      # Unknown type → Changed
      CHANGED_ENTRIES+=("$entry")
      ;;
  esac
}

# Process each commit
while IFS=$'\t' read -r hash subject author date; do
  parse_commit_message "$subject" "$author" "$date" "$hash"
done <<< "$COMMIT_LOG"

# ─── Generate CHANGELOG.md ──────────────────────────────────────────────
{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project are documented in this file."
  echo ""
  echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),"
  echo "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)."
  echo ""

  # Version header
  echo "## [${VERSION}] - ${DATE_RANGE:-unknown}"
  echo ""

  # Added
  if [[ ${#ADDED_ENTRIES[@]} -gt 0 ]]; then
    echo "### Added"
    echo ""
    for entry in "${ADDED_ENTRIES[@]}"; do
      echo "$entry"
    done
    echo ""
  fi

  # Fixed
  if [[ ${#FIXED_ENTRIES[@]} -gt 0 ]]; then
    echo "### Fixed"
    echo ""
    for entry in "${FIXED_ENTRIES[@]}"; do
      echo "$entry"
    done
    echo ""
  fi

  # Changed
  if [[ ${#CHANGED_ENTRIES[@]} -gt 0 ]]; then
    echo "### Changed"
    echo ""
    for entry in "${CHANGED_ENTRIES[@]}"; do
      echo "$entry"
    done
    echo ""
  fi

  # Removed
  if [[ ${#REMOVED_ENTRIES[@]} -gt 0 ]]; then
    echo "### Removed"
    echo ""
    for entry in "${REMOVED_ENTRIES[@]}"; do
      echo "$entry"
    done
    echo ""
  fi

  # Summary stats
  local_total=$(( ${#ADDED_ENTRIES[@]} + ${#FIXED_ENTRIES[@]} + ${#CHANGED_ENTRIES[@]} + ${#REMOVED_ENTRIES[@]} ))
  if [[ $local_total -eq 0 ]]; then
    echo "_No notable changes in this release._"
    echo ""
  fi

  # Link to compare
  if [[ -n "$LATEST_TAG" ]]; then
    REMOTE_URL=$(git -C "$GIT_DIR" remote get-url origin 2>/dev/null || true)
    if [[ -n "$REMOTE_URL" ]]; then
      # Normalize URL (strip .git suffix, convert git@ to https)
      CLEAN_URL="${REMOTE_URL%.git}"
      CLEAN_URL="${CLEAN_URL/git@github.com:/https:\/\/github.com\/}"
      if [[ "$CLEAN_URL" == https://github.com/* ]]; then
        echo "---"
        echo "[${LATEST_TAG}...${VERSION}]: ${CLEAN_URL}/compare/${LATEST_TAG}...${TO_REF}"
        echo ""
      fi
    fi
  fi

} > "$OUTPUT_FILE"

# ─── Report ──────────────────────────────────────────────────────────────
TOTAL=$(( ${#ADDED_ENTRIES[@]} + ${#FIXED_ENTRIES[@]} + ${#CHANGED_ENTRIES[@]} + ${#REMOVED_ENTRIES[@]} ))
echo "✅ Generated ${OUTPUT_FILE}"
echo "   Range: ${RANGE:-all commits}"
echo "   Total commits parsed: ${TOTAL}"
echo "   Added:   ${#ADDED_ENTRIES[@]}"
echo "   Fixed:   ${#FIXED_ENTRIES[@]}"
echo "   Changed: ${#CHANGED_ENTRIES[@]}"
echo "   Removed: ${#REMOVED_ENTRIES[@]}"
