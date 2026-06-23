#!/usr/bin/env bash
# changelog.sh — Generate structured CHANGELOG.md from git history
# Usage: ./changelog.sh [--output CHANGELOG.md] [--repo /path/to/repo]
#
# Auto-categorizes commits into: Added / Fixed / Changed / Removed / Documentation
# Uses conventional commit prefixes (feat:, fix:, chore:, docs:, refactor:, etc.)
# Falls back to keyword matching for non-conventional messages.

set -uo pipefail

OUTPUT="CHANGELOG.md"
REPO_DIR="."

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output) OUTPUT="$2"; shift 2 ;;
    --repo) REPO_DIR="$2"; shift 2 ;;
    *) echo "Usage: $0 [--output CHANGELOG.md] [--repo /path/to/repo]"; exit 1 ;;
  esac
done

# Resolve paths before cd
REPO_DIR="$(cd "$REPO_DIR" 2>/dev/null && pwd)" || { echo "Error: Cannot access repo directory: $REPO_DIR"; exit 1; }
if [[ "$OUTPUT" != /* ]]; then
  OUTPUT="$(pwd)/${OUTPUT}"
fi

cd "$REPO_DIR"

# Ensure we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "Error: Not a git repository"
  exit 1
fi

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
echo "Generating changelog since: ${LAST_TAG:-beginning of time}"

# Categorize a commit message
categorize() {
  local msg="$1"
  local lmsg="${msg,,}"

  # Conventional commit prefixes
  if [[ "$lmsg" =~ ^feat(\(.+\))?: ]]; then echo "Added"; return 0; fi
  if [[ "$lmsg" =~ ^fix(\(.+\))?: ]]; then echo "Fixed"; return 0; fi
  if [[ "$lmsg" =~ ^docs(\(.+\))?: ]]; then echo "Documentation"; return 0; fi
  if [[ "$lmsg" =~ ^refactor(\(.+\))?: ]]; then echo "Changed"; return 0; fi
  if [[ "$lmsg" =~ ^perf(\(.+\))?: ]]; then echo "Changed"; return 0; fi
  if [[ "$lmsg" =~ ^test(\(.+\))?: ]]; then echo "Changed"; return 0; fi
  if [[ "$lmsg" =~ ^chore(\(.+\))?: ]]; then echo "Changed"; return 0; fi
  if [[ "$lmsg" =~ ^style(\(.+\))?: ]]; then echo "Changed"; return 0; fi
  if [[ "$lmsg" =~ ^ci(\(.+\))?: ]]; then echo "Changed"; return 0; fi
  if [[ "$lmsg" =~ ^build(\(.+\))?: ]]; then echo "Changed"; return 0; fi
  if [[ "$lmsg" =~ ^revert: ]]; then echo "Removed"; return 0; fi
  if [[ "$lmsg" =~ ^remove ]]; then echo "Removed"; return 0; fi
  if [[ "$lmsg" =~ ^delete ]]; then echo "Removed"; return 0; fi
  if [[ "$lmsg" =~ ^add ]]; then echo "Added"; return 0; fi
  if [[ "$lmsg" =~ ^fix|bug|hotfix|patch ]]; then echo "Fixed"; return 0; fi
  if [[ "$lmsg" =~ ^update|^change|^improve|^migrate|^bump ]]; then echo "Changed"; return 0; fi

  echo "Changed"  # default
}

# Build output file
build_changelog() {
  local output_file="$1"

  # Write header
  {
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "---"
    echo ""
  } > "$output_file"

  local TAGS
  TAGS=$(git tag --sort=-v:refname 2>/dev/null || true)

  if [ -z "$TAGS" ]; then
    echo "## [Unreleased]" >> "$output_file"
    echo "" >> "$output_file"
    process_range "HEAD" "$output_file"
  else
    local PREV=""
    local TAG
    for TAG in $TAGS; do
      echo "## [${TAG}]" >> "$output_file"
      echo "" >> "$output_file"
      if [ -z "$PREV" ]; then
        process_range "${TAG}..HEAD" "$output_file"
      else
        process_range "${TAG}..${PREV}" "$output_file"
      fi
      PREV="$TAG"
    done

    local OLDEST FIRST
    OLDEST=$(echo "$TAGS" | tail -1)
    FIRST=$(git rev-list --max-parents=0 HEAD 2>/dev/null || echo "")
    if [ -n "$FIRST" ] && [ "$FIRST" != "$OLDEST" ]; then
      echo "## [Initial commits]" >> "$output_file"
      echo "" >> "$output_file"
      process_range "${FIRST}..${OLDEST}" "$output_file"
    fi
  fi
}

# Process a commit range and append categorized entries
process_range() {
  local range="$1"
  local output_file="$2"

  # Collect commits into a temp file to avoid set -e issues with process substitution
  local commit_file
  commit_file=$(mktemp)
  git log --pretty=format:"%s %h" --no-merges "$range" 2>/dev/null > "$commit_file" || true

  local added="" fixed="" changed="" removed="" docs=""
  local line msg hash cat entry

  while IFS= read -r line; do
    [ -z "$line" ] && continue
    # Split on last space to get hash
    hash="${line##* }"
    msg="${line% *}"
    [ -z "$msg" ] && continue
    cat=$(categorize "$msg")
    entry="  - ${msg} (${hash})"
    case "$cat" in
      Added) added="${added}"$'\n'"${entry}" ;;
      Fixed) fixed="${fixed}"$'\n'"${entry}" ;;
      Removed) removed="${removed}"$'\n'"${entry}" ;;
      Documentation) docs="${docs}"$'\n'"${entry}" ;;
      *) changed="${changed}"$'\n'"${entry}" ;;
    esac
  done < "$commit_file"

  rm -f "$commit_file"

  {
    [ -n "$added" ] && echo "### Added" && echo "${added}" && echo ""
    [ -n "$fixed" ] && echo "### Fixed" && echo "${fixed}" && echo ""
    [ -n "$changed" ] && echo "### Changed" && echo "${changed}" && echo ""
    [ -n "$removed" ] && echo "### Removed" && echo "${removed}" && echo ""
    [ -n "$docs" ] && echo "### Documentation" && echo "${docs}" && echo ""
  } >> "$output_file"
}

# Main
build_changelog "$OUTPUT"
echo "✓ Changelog written to ${OUTPUT} ($(wc -l < "$OUTPUT") lines)"
