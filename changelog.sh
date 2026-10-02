#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Categorizes commits using Conventional Commits prefixes:
#   feat/add → Added, fix → Fixed, refactor/perf/style/ci/build/chore/docs → Changed, revert/remove → Removed
# Usage: bash changelog.sh [--output FILE] [--since TAG] [--all] [--version VERSION]

set -euo pipefail

# ─── Defaults ──────────────────────────────────────────────
OUTPUT="CHANGELOG.md"
SINCE_TAG=""
ALL_COMMITS=false
VERSION=""

# ─── Argument parsing ─────────────────────────────────────
usage() {
  cat <<EOF
Usage: bash changelog.sh [OPTIONS]

Options:
  --output  FILE     Output file path (default: CHANGELOG.md)
  --since   TAG      Generate changelog since this tag (default: latest tag)
  --all              Include all commits (ignore tags)
  --version VERSION  Version header to use (default: Unreleased or tag-derived)
  -h, --help         Show this help message
EOF
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output)  OUTPUT="$2";  shift 2 ;;
    --since)   SINCE_TAG="$2"; shift 2 ;;
    --all)     ALL_COMMITS=true; shift ;;
    --version) VERSION="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# ─── Verify git repo ──────────────────────────────────────
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "Error: not inside a git repository." >&2
  exit 1
fi

# ─── Determine commit range ───────────────────────────────
if [[ "$ALL_COMMITS" == true ]]; then
  RANGE=""
  RANGE_DESC="all commits"
elif [[ -n "$SINCE_TAG" ]]; then
  if ! git rev-parse "$SINCE_TAG" &>/dev/null; then
    echo "Error: tag '$SINCE_TAG' not found." >&2
    exit 1
  fi
  RANGE="${SINCE_TAG}..HEAD"
  RANGE_DESC="commits since $SINCE_TAG"
else
  LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
  if [[ -n "$LATEST_TAG" ]]; then
    # Check if HEAD is pointing directly to LATEST_TAG
    TAG_HASH=$(git rev-parse -q --verify "refs/tags/${LATEST_TAG}^{commit}" 2>/dev/null || git rev-parse "$LATEST_TAG" 2>/dev/null || true)
    HEAD_HASH=$(git rev-parse HEAD 2>/dev/null || true)

    if [[ -n "$TAG_HASH" && "$TAG_HASH" == "$HEAD_HASH" ]]; then
      # HEAD is at the tag itself; collect commits included in this tag release
      PREV_TAG=$(git describe --tags --abbrev=0 "${LATEST_TAG}^" 2>/dev/null || true)
      if [[ -n "$PREV_TAG" ]]; then
        RANGE="${PREV_TAG}..${LATEST_TAG}"
        RANGE_DESC="commits for ${LATEST_TAG} (since ${PREV_TAG})"
      else
        RANGE="${LATEST_TAG}"
        RANGE_DESC="commits up to ${LATEST_TAG}"
      fi
      [[ -z "$VERSION" ]] && VERSION_HEADER="${LATEST_TAG}"
    else
      RANGE="${LATEST_TAG}..HEAD"
      RANGE_DESC="commits since $LATEST_TAG"
      [[ -z "$VERSION" ]] && VERSION_HEADER="Unreleased (since $LATEST_TAG)"
    fi
  else
    RANGE=""
    RANGE_DESC="all commits (no tags found)"
    [[ -z "$VERSION" ]] && VERSION_HEADER="Unreleased"
  fi
fi

# ─── Determine version header ─────────────────────────────
if [[ -n "$VERSION" ]]; then
  VERSION_HEADER="$VERSION"
elif [[ -z "${VERSION_HEADER:-}" ]]; then
  VERSION_HEADER="Unreleased"
fi

DATE=$(date +%Y-%m-%d)

# ─── Collect commits ──────────────────────────────────────
# Format: <hash>|<subject>
if [[ -n "$RANGE" ]]; then
  COMMITS=$(git log "$RANGE" --pretty=format:"%h|%s" --no-merges 2>/dev/null || true)
else
  COMMITS=$(git log --pretty=format:"%h|%s" --no-merges 2>/dev/null || true)
fi

if [[ -z "$COMMITS" ]]; then
  echo "No commits found for range: $RANGE_DESC"
  exit 0
fi

# ─── Categorize commits ───────────────────────────────────
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
OTHER=()

while IFS='|' read -r hash subject; do
  [[ -z "$hash" ]] && continue

  # Normalize: extract conventional commit prefix (case-insensitive)
  prefix=$(echo "$subject" | grep -oiE '^[a-z]+' | head -1 | tr '[:upper:]' '[:lower:]')

  # Clean subject: strip conventional commit prefix and scope for cleaner display
  clean_subject=$(echo "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]*\))?[!]?:\s*//')
  # If stripping failed or emptied the string, use original
  [[ -z "$clean_subject" ]] && clean_subject="$subject"

  entry="- ${clean_subject} (\`${hash}\`)"

  case "$prefix" in
    feat|add|feature)
      ADDED+=("$entry") ;;
    fix|bugfix|hotfix)
      FIXED+=("$entry") ;;
    refactor|perf|style|ci|build|chore|docs|test|improvement|update|improve)
      CHANGED+=("$entry") ;;
    revert|remove|delete|deprecate)
      REMOVED+=("$entry") ;;
    *)
      OTHER+=("$entry") ;;
  esac
done <<< "$COMMITS"

# ─── Generate CHANGELOG ───────────────────────────────────
{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project will be documented in this file."
  echo ""
  echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)."
  echo ""
  echo "## [${VERSION_HEADER}] — ${DATE}"
  echo ""

  if [[ ${#ADDED[@]} -gt 0 ]]; then
    echo "### Added"
    printf '%s\n' "${ADDED[@]}"
    echo ""
  fi

  if [[ ${#FIXED[@]} -gt 0 ]]; then
    echo "### Fixed"
    printf '%s\n' "${FIXED[@]}"
    echo ""
  fi

  if [[ ${#CHANGED[@]} -gt 0 ]]; then
    echo "### Changed"
    printf '%s\n' "${CHANGED[@]}"
    echo ""
  fi

  if [[ ${#REMOVED[@]} -gt 0 ]]; then
    echo "### Removed"
    printf '%s\n' "${REMOVED[@]}"
    echo ""
  fi

  if [[ ${#OTHER[@]} -gt 0 ]]; then
    echo "### Other"
    printf '%s\n' "${OTHER[@]}"
    echo ""
  fi

} > "$OUTPUT"

TOTAL=$(( ${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} + ${#OTHER[@]} ))
echo "✅ Generated ${OUTPUT} — ${TOTAL} commits categorized (${RANGE_DESC})"
echo "   Added: ${#ADDED[@]}, Fixed: ${#FIXED[@]}, Changed: ${#CHANGED[@]}, Removed: ${#REMOVED[@]}, Other: ${#OTHER[@]}"
