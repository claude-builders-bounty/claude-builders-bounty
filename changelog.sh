#!/usr/bin/env bash
set -euo pipefail

# ──────────────────────────────────────────────────
# changelog.sh — Generate CHANGELOG.md from git history
# Usage: bash changelog.sh [--output CHANGELOG.md] [--since v0.1.0]
# ──────────────────────────────────────────────────

OUTPUT="${CHANGELOG_OUTPUT:-CHANGELOG.md}"
SINCE_REF=""
REPO_PATH="."

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --output) OUTPUT="$2"; shift 2 ;;
    --since) SINCE_REF="$2"; shift 2 ;;
    --help|-h)
      echo "Usage: bash changelog.sh [--output CHANGELOG.md] [--since v0.1.0] [repo-path]"
      exit 0 ;;
    *)
      if [[ -d "$1" ]]; then
        REPO_PATH="$1"
      else
        echo "Unknown option or invalid path: $1" >&2
        exit 1
      fi
      shift ;;
  esac
done

# Check we're in a git repo
if ! git -C "$REPO_PATH" rev-parse --git-dir > /dev/null 2>&1; then
  echo "Error: Not a git repository: $REPO_PATH" >&2
  exit 1
fi

# Determine the range
if [[ -z "$SINCE_REF" ]]; then
  # Get the latest tag, or fall back to first commit
  LATEST_TAG=$(git -C "$REPO_PATH" describe --tags --abbrev=0 2>/dev/null || true)
  if [[ -n "$LATEST_TAG" ]]; then
    SINCE_REF="$LATEST_TAG"
  else
    SINCE_REF=$(git -C "$REPO_PATH" rev-list --max-parents=0 HEAD 2>/dev/null || echo "HEAD~0")
  fi
fi

# Get commits since the ref
COMMITS=$(git -C "$REPO_PATH" log "$SINCE_REF..HEAD" --format="%s|||%h|||%an|||%ai" --no-merges 2>/dev/null || true)

# If no commits since tag, try all commits as fallback
if [[ -z "$COMMITS" ]]; then
  COMMITS=$(git -C "$REPO_PATH" log --format="%s|||%h|||%an|||%ai" --no-merges 2>/dev/null || true)
fi

if [[ -z "$COMMITS" ]]; then
  echo "No commits found." >&2
  echo "# Changelog" > "$OUTPUT"
  echo "" >> "$OUTPUT"
  echo "_No commits found._" >> "$OUTPUT"
  echo "✅ Created $OUTPUT (empty)"
  exit 0
fi

# Categories with regex patterns
CAT_COMMIT_RANGE="$SINCE_REF..HEAD"

# Parse commits
ADDED=""; FIXED=""; CHANGED=""; REMOVED=""; DOCS=""; SECURITY=""; DEPS=""; OTHER=""

while IFS= read -r LINE; do
  [[ -z "$LINE" ]] && continue
  MSG="${LINE%%|||*}"
  REST="${LINE#*|||}"
  HASH="${REST%%|||*}"
  REST="${REST#*|||}"
  AUTHOR="${REST%%|||*}"
  DATE="${REST#*|||}"

  # Clean up commit subject — strip conventional commit prefix
  CLEAN_MSG=$(echo "$MSG" | sed -E 's/^[a-zA-Z]+(\([^)]*\))?!?:[[:space:]]*//')
  # Remove trailing punctuation
  CLEAN_MSG=$(echo "$CLEAN_MSG" | sed -E 's/[[:space:]]*[.！。]+$//')
  # Capitalize first letter
  FIRST=$(echo "${CLEAN_MSG:0:1}" | tr '[:lower:]' '[:upper:]')
  CLEAN_MSG="${FIRST}${CLEAN_MSG:1}"

  # Get remote for linking
  REMOTE_URL=$(git -C "$REPO_PATH" remote get-url origin 2>/dev/null || echo "")
  REMOTE_CLEAN=$(echo "$REMOTE_URL" | sed 's/.*github.com[:\/]//;s/\.git$//' 2>/dev/null || echo "")
  [[ -z "$REMOTE_CLEAN" ]] && COMMIT_LINK="" || COMMIT_LINK="(https://github.com/${REMOTE_CLEAN}/commit/${HASH})"
  [[ -n "$COMMIT_LINK" ]] && ENTRY="  - ${CLEAN_MSG} ${COMMIT_LINK}" || ENTRY="  - ${CLEAN_MSG}"

  if echo "$MSG" | grep -qiE "^feat|^feature|^add|^new|^implement"; then
    ADDED="${ADDED}${ENTRY}\n"
  elif echo "$MSG" | grep -qiE "^fix|^bug|^hotfix|^patch|^correct"; then
    FIXED="${FIXED}${ENTRY}\n"
  elif echo "$MSG" | grep -qiE "^refactor|^update|^change|^improve|^upgrade|^migrate|^perf"; then
    CHANGED="${CHANGED}${ENTRY}\n"
  elif echo "$MSG" | grep -qiE "^remove|^delete|^drop|^deprecate"; then
    REMOVED="${REMOVED}${ENTRY}\n"
  elif echo "$MSG" | grep -qiE "^docs|^doc|^readme"; then
    DOCS="${DOCS}${ENTRY}\n"
  elif echo "$MSG" | grep -qiE "^security|^vuln|^cve"; then
    SECURITY="${SECURITY}${ENTRY}\n"
  elif echo "$MSG" | grep -qiE "^deps|^bump|^chore\(deps"; then
    DEPS="${DEPS}${ENTRY}\n"
  else
    OTHER="${OTHER}${ENTRY}\n"
  fi
done <<< "$COMMITS"

# Get version and date info
VERSION=$(git -C "$REPO_PATH" describe --tags --abbrev=0 2>/dev/null || echo "Unreleased")
CURRENT_DATE=$(date +%Y-%m-%d)

# Write CHANGELOG.md
{
  echo "# Changelog"
  echo ""
  echo "## [${VERSION}] - ${CURRENT_DATE}"
  echo ""

  HAS_CONTENT=false

  if [[ -n "${ADDED// }" ]]; then
    echo "### Added"
    echo -e "$ADDED" | sed '/^[[:space:]]*$/d'
    echo ""
    HAS_CONTENT=true
  fi

  if [[ -n "${FIXED// }" ]]; then
    echo "### Fixed"
    echo -e "$FIXED" | sed '/^[[:space:]]*$/d'
    echo ""
    HAS_CONTENT=true
  fi

  if [[ -n "${CHANGED// }" ]]; then
    echo "### Changed"
    echo -e "$CHANGED" | sed '/^[[:space:]]*$/d'
    echo ""
    HAS_CONTENT=true
  fi

  if [[ -n "${REMOVED// }" ]]; then
    echo "### Removed"
    echo -e "$REMOVED" | sed '/^[[:space:]]*$/d'
    echo ""
    HAS_CONTENT=true
  fi

  if [[ -n "${DOCS// }" ]]; then
    echo "### Documentation"
    echo -e "$DOCS" | sed '/^[[:space:]]*$/d'
    echo ""
    HAS_CONTENT=true
  fi

  if [[ -n "${SECURITY// }" ]]; then
    echo "### Security"
    echo -e "$SECURITY" | sed '/^[[:space:]]*$/d'
    echo ""
    HAS_CONTENT=true
  fi

  if [[ -n "${DEPS// }" ]]; then
    echo "### Dependencies"
    echo -e "$DEPS" | sed '/^[[:space:]]*$/d'
    echo ""
    HAS_CONTENT=true
  fi

  if [[ -n "${OTHER// }" ]]; then
    echo "### Other"
    echo -e "$OTHER" | sed '/^[[:space:]]*$/d'
    echo ""
    HAS_CONTENT=true
  fi

  if [[ "$HAS_CONTENT" == false ]]; then
    echo "_No changes since last release._"
    echo ""
  fi

  echo "---"
  echo "_Generated by [changelog.sh](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1)_"
} > "$OUTPUT"

COUNT=$(grep -c '  - ' "$OUTPUT" 2>/dev/null || echo 0)
echo "✅ CHANGELOG.md generated at $OUTPUT (${COUNT} entries)"
