#!/usr/bin/env bash
#
# changelog.sh — Generate a structured CHANGELOG.md from git history
#
# Usage:
#   ./changelog.sh              # Writes CHANGELOG.md
#   ./changelog.sh --output=FILE  # Writes to FILE
#   ./changelog.sh --since=v1.0.0 # Use a specific tag/ref as starting point
#   ./changelog.sh --dry-run      # Print to stdout instead of writing
#
# Requirements: git (must be run inside a git repository)

set -euo pipefail

# ── Defaults ────────────────────────────────────────────────────────────────
OUTPUT_FILE="CHANGELOG.md"
DRY_RUN=false
SINCE_REF=""

# ── Parse arguments ─────────────────────────────────────────────────────────
for arg in "$@"; do
  case "$arg" in
    --output=*)
      OUTPUT_FILE="${arg#*=}"
      ;;
    --since=*)
      SINCE_REF="${arg#*=}"
      ;;
    --dry-run)
      DRY_RUN=true
      ;;
    --help|-h)
      echo "Usage: $0 [--output=FILE] [--since=TAG] [--dry-run]"
      echo ""
      echo "Generate a structured CHANGELOG.md from git history."
      echo ""
      echo "Options:"
      echo "  --output=FILE   Output file (default: CHANGELOG.md)"
      echo "  --since=TAG     Start from a specific tag/ref (default: last tag)"
      echo "  --dry-run       Print to stdout instead of writing to file"
      echo "  --help, -h      Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $arg"
      echo "Use --help for usage information."
      exit 1
      ;;
  esac
done

# ── Verify we're in a git repo ──────────────────────────────────────────────
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "Error: Not a git repository. Run this script from inside a git project."
  exit 1
fi

# ── Determine the ref range ────────────────────────────────────────────────
if [[ -z "$SINCE_REF" ]]; then
  # Find the latest tag
  LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
  if [[ -n "$LATEST_TAG" ]]; then
    SINCE_REF="$LATEST_TAG"
    echo "[INFO] Using latest tag: $LATEST_TAG" >&2
  else
    echo "[INFO] No tags found — including all commits." >&2
  fi
fi

# ── Get repository info ─────────────────────────────────────────────────────
REPO_URL=$(git remote get-url origin 2>/dev/null || echo "")
# Normalize SSH URLs to HTTPS for markdown links
if [[ "$REPO_URL" =~ ^git@(.+):(.+)\.git$ ]]; then
  REPO_URL="https://${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
elif [[ "$REPO_URL" =~ ^https://(.+)\.git$ ]]; then
  REPO_URL="https://${BASH_REMATCH[1]}"
fi

# ── Fetch commits ───────────────────────────────────────────────────────────
if [[ -n "$SINCE_REF" ]]; then
  # Check if the tag/ref actually exists
  if git rev-parse --verify "$SINCE_REF" > /dev/null 2>&1; then
    COMMITS=$(git log "$SINCE_REF"..HEAD --format="%H|||%s|||%an|||%aI" --no-merges 2>/dev/null || true)
    RANGE_DESC="$SINCE_REF..HEAD"
  else
    echo "[WARN] Tag '$SINCE_REF' not found — including all commits." >&2
    COMMITS=$(git log --format="%H|||%s|||%an|||%aI" --no-merges 2>/dev/null || true)
    RANGE_DESC="all commits"
  fi
else
  COMMITS=$(git log --format="%H|||%s|||%an|||%aI" --no-merges 2>/dev/null || true)
  RANGE_DESC="all commits"
fi

# ── If no commits found ─────────────────────────────────────────────────────
if [[ -z "$COMMITS" ]]; then
  echo "[INFO] No commits found in range: $RANGE_DESC" >&2
  exit 0
fi

# ── Get version / date ──────────────────────────────────────────────────────
HEAD_TAG=$(git describe --tags --exact-match HEAD 2>/dev/null || echo "")
RELEASE_TAG="${HEAD_TAG:-$(git describe --tags --abbrev=0 2>/dev/null || echo "Unreleased")}"
RELEASE_DATE=$(git log -1 --format="%as" HEAD 2>/dev/null || date +%Y-%m-%d)

# ── Categorize commits ──────────────────────────────────────────────────────
# Heuristic: parse commit messages for conventional commit prefixes
# or keywords in the message body

ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
OTHER=()

while IFS= read -r line; do
  [[ -z "$line" ]] && continue

  IFS='|||' read -r sha message author date <<< "$line"
  short_sha="${sha:0:7}"

  # Normalize to lowercase for matching
  msg_lower="${message,,}"

  # Categorization rules (conventional commits + keyword matching)
  if [[ "$msg_lower" =~ ^feat(\\([^)]*\))?!?: ]] || \
     [[ "$msg_lower" =~ ^add ]] || \
     [[ "$msg_lower" =~ ^implement ]] || \
     [[ "$msg_lower" =~ ^create ]] || \
     [[ "$msg_lower" =~ ^introduce ]]; then
    ADDED+=("$message|$short_sha|$author")
  elif [[ "$msg_lower" =~ ^fix(\\([^)]*\))?!?: ]] || \
       [[ "$msg_lower" =~ ^bugfix ]] || \
       [[ "$msg_lower" =~ ^hotfix ]] || \
       [[ "$msg_lower" =~ ^patch ]] || \
       [[ "$msg_lower" =~ ^correct ]] || \
       [[ "$msg_lower" =~ ^resolve ]] || \
       [[ "$msg_lower" =~ ^repair ]]; then
    FIXED+=("$message|$short_sha|$author")
  elif [[ "$msg_lower" =~ ^refactor(\\([^)]*\))?!?: ]] || \
       [[ "$msg_lower" =~ ^update ]] || \
       [[ "$msg_lower" =~ ^upgrade ]] || \
       [[ "$msg_lower" =~ ^migrate ]] || \
       [[ "$msg_lower" =~ ^rework ]] || \
       [[ "$msg_lower" =~ ^redesign ]] || \
       [[ "$msg_lower" =~ ^improve ]] || \
       [[ "$msg_lower" =~ ^change ]]; then
    CHANGED+=("$message|$short_sha|$author")
  elif [[ "$msg_lower" =~ ^remove ]] || \
       [[ "$msg_lower" =~ ^delete ]] || \
       [[ "$msg_lower" =~ ^deprecate ]] || \
       [[ "$msg_lower" =~ ^drop ]]; then
    REMOVED+=("$message|$short_sha|$author")
  else
    OTHER+=("$message|$short_sha|$author")
  fi
done <<< "$COMMITS"

# ── Build CHANGELOG content ─────────────────────────────────────────────────
changelog="# Changelog\n\n"
changelog+="All notable changes to this project will be documented in this file.\n\n"
changelog+="The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),\n"
changelog+="and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n\n"
changelog+="---\n\n"

# Release header
changelog+="## [${RELEASE_TAG}] - ${RELEASE_DATE}\n\n"

# Helper to render a section
render_section() {
  local title="$1"
  local emoji="$2"
  shift 2
  local -a items=("$@")

  if [[ ${#items[@]} -gt 0 ]]; then
    echo "" >> "$TEMP_FILE"
    echo "### ${emoji} ${title}" >> "$TEMP_FILE"
    echo "" >> "$TEMP_FILE"
    for item in "${items[@]}"; do
      IFS='|' read -r msg sha author <<< "$item"
      if [[ -n "$REPO_URL" ]]; then
        echo "- ${msg} ([${sha}](${REPO_URL}/commit/${sha}))" >> "$TEMP_FILE"
      else
        echo "- ${msg} (${sha})" >> "$TEMP_FILE"
      fi
    done
  fi
}

# Build into a temp file first (for proper newline handling)
TEMP_FILE=$(mktemp)
trap "rm -f $TEMP_FILE" EXIT

if [[ ${#ADDED[@]} -gt 0 ]] || [[ ${#FIXED[@]} -gt 0 ]] || [[ ${#CHANGED[@]} -gt 0 ]] || [[ ${#REMOVED[@]} -gt 0 ]] || [[ ${#OTHER[@]} -gt 0 ]]; then
  : # At least one section exists
fi

render_section "Added" "✨" "${ADDED[@]:+${ADDED[@]}}"
render_section "Fixed" "🐛" "${FIXED[@]:+${FIXED[@]}}"
render_section "Changed" "🔄" "${CHANGED[@]:+${CHANGED[@]}}"
render_section "Removed" "🗑️" "${REMOVED[@]:+${REMOVED[@]}}"

# Unclassified commits go to "Other"
if [[ ${#OTHER[@]} -gt 0 ]]; then
  render_section "Other" "📦" "${OTHER[@]:+${OTHER[@]}}"
fi

# Read the temp file back
ADDED_CONTENT=$(cat "$TEMP_FILE")

changelog+="$ADDED_CONTENT"

# Footer with stats
changelog+="\n---\n"
changelog+="\n_${#ADDED[@]} added | ${#FIXED[@]} fixed | ${#CHANGED[@]} changed | ${#REMOVED[@]} removed_\n"

# ── Output ──────────────────────────────────────────────────────────────────
if [[ "$DRY_RUN" == true ]]; then
  echo -e "$changelog"
else
  echo -e "$changelog" > "$OUTPUT_FILE"
  echo "[OK] CHANGELOG written to $OUTPUT_FILE" >&2
fi
