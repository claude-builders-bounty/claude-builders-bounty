#!/usr/bin/env bash
#
# changelog.sh — Generate a structured CHANGELOG.md from git history
#
# Usage:
#   bash changelog.sh [OPTIONS]
#
# Options:
#   --since-tag <tag>   Start from this tag (default: last git tag)
#   --output <file>     Output file (default: CHANGELOG.md)
#   --repo <path>       Path to git repo (default: .)
#   --dry-run           Print to stdout instead of file
#   -h, --help          Show this help message
#
set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────
SINCE_TAG=""
OUTPUT="CHANGELOG.md"
REPO_PATH="."
DRY_RUN=false

# ── Parse Arguments ───────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --since-tag)  SINCE_TAG="$2"; shift 2 ;;
    --output)     OUTPUT="$2";    shift 2 ;;
    --repo)       REPO_PATH="$2"; shift 2 ;;
    --dry-run)    DRY_RUN=true;   shift   ;;
    -h|--help)
      sed -n '2,15p' "$0"
      exit 0
      ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# ── Helpers ───────────────────────────────────────────────────────────
cd "$REPO_PATH"

if ! git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "Error: not a git repository" >&2
  exit 1
fi

# Determine the starting tag
if [[ -z "$SINCE_TAG" ]]; then
  SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

# Build the commit range
if [[ -n "$SINCE_TAG" ]]; then
  RANGE="${SINCE_TAG}..HEAD"
  VERSION="Unreleased"
  # Try to derive the next version
  TAG_VERSION="${SINCE_TAG#v}"
else
  RANGE="HEAD"
  VERSION="Unreleased"
  TAG_VERSION="0.0.0"
fi

# ── Categorize Commits ────────────────────────────────────────────────
declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()
declare -a OTHER=()

categorize() {
  local hash="$1"
  local subject="$2"
  local entry="- ${subject}"

  # Lowercase for matching
  local lower
  lower=$(echo "$subject" | tr '[:upper:]' '[:lower:]')

  # Conventional commit prefixes
  if [[ "$lower" =~ ^feat(\(.+\))?: ]]; then
    ADDED+=("$entry")
  elif [[ "$lower" =~ ^(fix|bugfix|hotfix)(\(.+\))?: ]]; then
    FIXED+=("$entry")
  elif [[ "$lower" =~ ^(refactor|update|change|improve|modify)(\(.+\))?: ]]; then
    CHANGED+=("$entry")
  elif [[ "$lower" =~ ^(remove|delete|drop|deprecate)(\(.+\))?: ]]; then
    REMOVED+=("$entry")
  # Keyword detection for non-conventional commits
  elif [[ "$lower" =~ ^(add|new|create|introduce|implement|support) ]]; then
    ADDED+=("$entry")
  elif [[ "$lower" =~ ^(fix|resolve|repair|patch|correct|handle) ]]; then
    FIXED+=("$entry")
  elif [[ "$lower" =~ ^(update|change|modify|improve|adjust|refactor|migrate|upgrade) ]]; then
    CHANGED+=("$entry")
  elif [[ "$lower" =~ ^(remove|delete|drop|deprecate|eliminate|strip) ]]; then
    REMOVED+=("$entry")
  else
    OTHER+=("$entry")
  fi
}

# Read commits
while IFS=$'\t' read -r hash subject; do
  categorize "$hash" "$subject"
done < <(git log "$RANGE" --pretty=format:"%h%x09%s" --no-merges 2>/dev/null)

# ── Build the Changelog ───────────────────────────────────────────────
build_section() {
  local title="$1"
  shift
  local items=("$@")

  if [[ ${#items[@]} -gt 0 ]]; then
    echo ""
    echo "### ${title}"
    for item in "${items[@]}"; do
      echo "$item"
    done
  fi
}

{
  echo "# Changelog"
  echo ""
  echo "## [${VERSION}]"
  echo ""

  if [[ -n "$SINCE_TAG" ]]; then
    echo "> Comparing ${SINCE_TAG}...HEAD"
    echo ""
  fi

  build_section "Added"    "${ADDED[@]}"
  build_section "Fixed"    "${FIXED[@]}"
  build_section "Changed"  "${CHANGED[@]}"
  build_section "Removed"  "${REMOVED[@]}"
  build_section "Other"    "${OTHER[@]}"

  echo ""
} > /tmp/changelog_output.md

# ── Output ────────────────────────────────────────────────────────────
if [[ "$DRY_RUN" == true ]]; then
  cat /tmp/changelog_output.md
else
  # If CHANGELOG.md already exists, prepend the new section
  if [[ -f "$OUTPUT" ]]; then
    # Read existing content (skip the # Changelog header if present)
    existing=$(tail -n +2 "$OUTPUT")
    {
      cat /tmp/changelog_output.md
      echo ""
      echo "$existing"
    } > "$OUTPUT"
  else
    cp /tmp/changelog_output.md "$OUTPUT"
  fi
  echo "✅ Changelog written to ${OUTPUT}"
fi

rm -f /tmp/changelog_output.md
