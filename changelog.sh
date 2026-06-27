#!/usr/bin/env bash
# ============================================================
# changelog.sh — Auto-generate CHANGELOG.md from git history
# ============================================================
# Fetches commits since the last git tag, auto-categorizes
# into Added / Fixed / Changed / Removed, and outputs a
# properly formatted CHANGELOG.md.
#
# Usage:
#   bash changelog.sh                  # generate CHANGELOG.md in current dir
#   bash changelog.sh --stdout         # print to stdout instead
#   bash changelog.sh --from v1.0.0    # start from a specific tag
#   bash changelog.sh --to HEAD~5      # end at a specific ref
# ============================================================
set -euo pipefail

# ── Colours ────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Colour

# ── Defaults ────────────────────────────────────────────────
OUTPUT_FILE="CHANGELOG.md"
FROM_TAG=""       # —from: start tag (auto-detected if empty)
TO_REF="HEAD"     # —to:   end ref
PRINT_STDOUT=false

# ── Parse args ──────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --stdout)      PRINT_STDOUT=true; shift ;;
    --from)        FROM_TAG="$2"; shift 2 ;;
    --to)          TO_REF="$2";    shift 2 ;;
    --help|-h)
      echo "Usage: bash changelog.sh [--stdout] [--from TAG] [--to REF]"
      echo ""
      echo "  --stdout       Print to stdout instead of writing CHANGELOG.md"
      echo "  --from TAG     Start from TAG (default: latest tag before HEAD)"
      echo "  --to   REF     End at REF (default: HEAD)"
      exit 0
      ;;
    *) echo -e "${RED}Unknown option: $1${NC}"; exit 1 ;;
  esac
done

# ── Pre-flight checks ───────────────────────────────────────
if ! command -v git &>/dev/null; then
  echo -e "${RED}Error: git is not installed.${NC}" >&2
  exit 1
fi

if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo -e "${RED}Error: not inside a git repository.${NC}" >&2
  exit 1
fi

# ── Auto-detect tag range ──────────────────────────────────
if [[ -z "$FROM_TAG" ]]; then
  # Find the most recent tag reachable from HEAD
  FROM_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
  if [[ -z "$FROM_TAG" ]]; then
    # No tags at all — use the initial commit
    FROM_TAG=$(git rev-list --max-parents=0 HEAD 2>/dev/null || echo "")
    if [[ -z "$FROM_TAG" ]]; then
      echo -e "${RED}Error: no commits found.${NC}" >&2
      exit 1
    fi
    echo -e "${YELLOW}No tags found — using initial commit ${FROM_TAG:0:7} as boundary.${NC}" >&2
  else
    echo -e "${CYAN}Last tag: ${FROM_TAG}${NC}" >&2
  fi
fi

# ── Gather commits ──────────────────────────────────────────
# Format: <short_hash>|<subject>
COMMITS=$(git log "${FROM_TAG}..${TO_REF}" \
  --pretty=format:"%h|%s" \
  --no-merges 2>/dev/null || true)

if [[ -z "$COMMITS" ]]; then
  echo -e "${YELLOW}No new commits since ${FROM_TAG}. CHANGELOG is empty.${NC}" >&2
  if $PRINT_STDOUT; then
    echo ""
  else
    echo "# Changelog" > "$OUTPUT_FILE"
    echo "" >> "$OUTPUT_FILE"
    echo "No new changes since **${FROM_TAG}**." >> "$OUTPUT_FILE"
    echo -e "${GREEN}✓ Wrote ${OUTPUT_FILE}${NC}" >&2
  fi
  exit 0
fi

# ── Categorise commits ──────────────────────────────────────
categorise() {
  local msg="$1"
  # Normalise to lowercase for pattern matching
  local lower="${msg,,}"

  # Conventional commits prefix detection
  if [[ "$lower" =~ ^feat(\(.*\))?!?[:]?[[:space:]]* ]]; then
    echo "Added"
  elif [[ "$lower" =~ ^fix(\(.*\))?!?[:]?[[:space:]]* ]]; then
    echo "Fixed"
  elif [[ "$lower" =~ ^breaking[[:space:]]change(\(.*\))?!?[:]?[[:space:]]* ]]; then
    echo "Changed"
  elif [[ "$lower" =~ ^refactor(\(.*\))?!?[:]?[[:space:]]* ]]; then
    echo "Changed"
  elif [[ "$lower" =~ ^perf(\(.*\))?!?[:]?[[:space:]]* ]]; then
    echo "Changed"
  elif [[ "$lower" =~ ^revert(\(.*\))?!?[:]?[[:space:]]* ]]; then
    echo "Fixed"
  elif [[ "$lower" =~ ^remove(\(.*\))?!?[:]?[[:space:]]* ]]; then
    echo "Removed"
  elif [[ "$lower" =~ ^chore(\(.*\))?!?[:]?[[:space:]]* ]]; then
    echo "Changed"
  elif [[ "$lower" =~ ^docs(\(.*\))?!?[:]?[[:space:]]* ]]; then
    echo "Changed"
  elif [[ "$lower" =~ ^style(\(.*\))?!?[:]?[[:space:]]* ]]; then
    echo "Changed"
  elif [[ "$lower" =~ ^test(\(.*\))?!?[:]?[[:space:]]* ]]; then
    echo "Changed"
  elif [[ "$lower" =~ ^ci(\(.*\))?!?[:]?[[:space:]]* ]]; then
    echo "Changed"
  elif [[ "$lower" =~ ^build(\(.*\))?!?[:]?[[:space:]]* ]]; then
    echo "Changed"
  elif [[ "$lower" =~ ^remove(\(.*\))?!?[:]?[[:space:]]* ]]; then
    echo "Removed"
  elif [[ "$lower" =~ ^delete(\(.*\))?!?[:]?[[:space:]]* ]]; then
    echo "Removed"
  elif [[ "$lower" =~ ^deprecate(\(.*\))?!?[:]?[[:space:]]* ]]; then
    echo "Removed"
  # Keyword-based fallback
  elif [[ "$lower" =~ \b(add|new|feature|create|implement|introduce)\b ]]; then
    echo "Added"
  elif [[ "$lower" =~ \b(fix|bug|patch|hotfix|correct|resolve|repair)\b ]]; then
    echo "Fixed"
  elif [[ "$lower" =~ \b(remov|deprecat|delete|drop|eliminate)\b ]]; then
    echo "Removed"
  else
    echo "Changed"
  fi
}

# Strip conventional-commit prefix for display
strip_prefix() {
  local msg="$1"
  # Remove feat:, fix:, chore:, etc. including optional scope and breaking marker
  # Also keep the colon + space
  local stripped
  stripped=$(echo "$msg" | sed -E 's/^(feat|fix|chore|docs|refactor|perf|test|style|ci|build|revert|remove|breaking change)(\([^)]*\))?!?\s*:\s*//i')
  # If stripping removed everything (e.g. "fix: " → ""), restore original
  if [[ -z "$stripped" ]]; then
    echo "$msg"
  else
    echo "$stripped"
  fi
}

# Initialise category arrays
ADDED=()
FIXED=()
CHANGED=()
REMOVED=()

while IFS='|' read -r hash msg; do
  [[ -z "$hash" ]] && continue
  cat=$(categorise "$msg")
  display_msg=$(strip_prefix "$msg")
  # Capitalise first letter of display message
  display_msg="$(tr '[:lower:]' '[:upper:]' <<< "${display_msg:0:1}")${display_msg:1}"
  entry="- ${display_msg} ([${hash}]($(git remote get-url origin 2>/dev/null || echo "#")/commit/${hash}))"

  case "$cat" in
    Added)   ADDED+=("$entry")   ;;
    Fixed)   FIXED+=("$entry")   ;;
    Removed) REMOVED+=("$entry") ;;
    *)       CHANGED+=("$entry") ;;
  esac
done <<< "$COMMITS"

# ── Build version header ────────────────────────────────────
# Use the next tag suggestion: increment patch of last tag, or "0.1.0"
NEXT_VERSION=""
if [[ "$FROM_TAG" =~ ^v?([0-9]+)\.([0-9]+)\.([0-9]+) ]]; then
  NEXT_VERSION="v${BASH_REMATCH[1]}.${BASH_REMATCH[2]}.$((BASH_REMATCH[3] + 1))"
else
  NEXT_VERSION="v0.1.0"
fi

DATE=$(date +"%Y-%m-%d")

# ── Build output ────────────────────────────────────────────
build_changelog() {
  echo "# Changelog"
  echo ""
  echo "## [${NEXT_VERSION}] - ${DATE}"
  echo ""

  if [[ ${#ADDED[@]} -gt 0 ]]; then
    echo "### Added"
    for entry in "${ADDED[@]}"; do echo "$entry"; done
    echo ""
  fi

  if [[ ${#FIXED[@]} -gt 0 ]]; then
    echo "### Fixed"
    for entry in "${FIXED[@]}"; do echo "$entry"; done
    echo ""
  fi

  if [[ ${#CHANGED[@]} -gt 0 ]]; then
    echo "### Changed"
    for entry in "${CHANGED[@]}"; do echo "$entry"; done
    echo ""
  fi

  if [[ ${#REMOVED[@]} -gt 0 ]]; then
    echo "### Removed"
    for entry in "${REMOVED[@]}"; do echo "$entry"; done
    echo ""
  fi

  # Summary
  total=$((${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]}))
  echo "---"
  echo "_${total} change(s) since ${FROM_TAG}_"
}

# ── Output ──────────────────────────────────────────────────
if $PRINT_STDOUT; then
  build_changelog
else
  build_changelog > "$OUTPUT_FILE"
  echo -e "${GREEN}✓ Generated ${OUTPUT_FILE}${NC}" >&2
  echo -e "  ${CYAN}Version:${NC} ${NEXT_VERSION}" >&2
  echo -e "  ${CYAN}Changes:${NC} ${#ADDED[@]} added, ${#FIXED[@]} fixed, ${#CHANGED[@]} changed, ${#REMOVED[@]} removed" >&2
fi
