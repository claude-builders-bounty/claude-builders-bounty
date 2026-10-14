#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG from git history
# Usage:
#   bash changelog.sh [--repo <path>] [--from <ref>] [--to <ref>] [--output <file>] [--version <version>] [--date <YYYY-MM-DD>]
#
# Defaults:
#   --repo    current directory
#   --from    last git tag reachable from HEAD (fallback: root commit)
#   --to      HEAD
#   --output  CHANGELOG.md in the repo root
#   --version Unreleased
#   --date    today (YYYY-MM-DD)
#
# Categorization (documented in README.md):
#   feat:                                   → Added
#   fix:                                    → Fixed
#   remove/revert types, or remove/delete/drop/deprecate keywords → Removed
#   refactor/perf/style/chore/docs/test/build/ci + everything else → Changed
#   Non-conventional subjects are matched by keywords, else Changed. Nothing is dropped.
#   Merge commits (subject starting "Merge ") are skipped.

set -euo pipefail

REPO="."
FROM_REF=""
TO_REF="HEAD"
OUTPUT=""
VERSION="Unreleased"
DATE_OVERRIDE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)    REPO="$2"; shift 2 ;;
    --from)    FROM_REF="$2"; shift 2 ;;
    --to)      TO_REF="$2"; shift 2 ;;
    --output)  OUTPUT="$2"; shift 2 ;;
    --version) VERSION="$2"; shift 2 ;;
    --date)    DATE_OVERRIDE="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash changelog.sh [--repo <path>] [--from <ref>] [--to <ref>] [--output <file>] [--version <version>] [--date <YYYY-MM-DD>]"
      exit 0
      ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

# Resolve repo
REPO="$(cd "$REPO" && pwd)"
cd "$REPO"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: $REPO is not a git repository." >&2
  exit 1
fi

# Default output path
if [[ -z "$OUTPUT" ]]; then
  OUTPUT="$REPO/CHANGELOG.md"
fi

# Determine FROM ref
RANGE_NOTE=""
if [[ -z "$FROM_REF" ]]; then
  # Last tag reachable from HEAD
  LAST_TAG="$(git describe --tags --abbrev=0 "$TO_REF" 2>/dev/null || true)"
  if [[ -n "$LAST_TAG" ]]; then
    FROM_REF="$LAST_TAG"
    RANGE_NOTE="since last tag $LAST_TAG"
  else
    # No tags: fall back to root commit
    ROOT="$(git rev-list --max-parents=0 "$TO_REF" 2>/dev/null | head -n 1 || true)"
    if [[ -z "$ROOT" ]]; then
      echo "Error: no commits found in repository." >&2
      exit 1
    fi
    FROM_REF="$ROOT"
    RANGE_NOTE="no tags found; using all commits from root $ROOT"
  fi
else
  RANGE_NOTE="from $FROM_REF (explicit)"
fi

RANGE="$FROM_REF..$TO_REF"

# If FROM is the root commit itself, include it (root..HEAD excludes root)
# Detect: if FROM_REF is a root commit and user didn't pass explicit --from covering it,
# use "$FROM_REF^..$TO_REF" trick via --root handling. Simpler: if FROM is root, use full range.
IS_ROOT=false
if git rev-list --max-parents=0 "$TO_REF" 2>/dev/null | grep -qx "$FROM_REF"; then
  IS_ROOT=true
fi

DATE_STR="${DATE_OVERRIDE:-$(date +%Y-%m-%d)}"

# Fetch commit subjects (one per line), newest first
declare -a RAW_SUBJECTS=()
if [[ "$IS_ROOT" == true && "$RANGE_NOTE" == *"no tags found"* ]]; then
  # Include root commit
  while IFS= read -r line; do
    RAW_SUBJECTS+=("$line")
  done < <(git log "$TO_REF" --pretty=tformat:'%s' 2>/dev/null || true)
  RANGE="$FROM_REF (root)..$TO_REF [inclusive]"
else
  while IFS= read -r line; do
    RAW_SUBJECTS+=("$line")
  done < <(git log "$RANGE" --pretty=tformat:'%s' 2>/dev/null || true)
fi

echo "Generating changelog: $RANGE_NOTE, range $FROM_REF..$TO_REF" >&2

# Category buckets
declare -a ADDED=() FIXED=() CHANGED=() REMOVED=()

# Helper: lowercase a string (bash 4+)
lowercase() {
  echo "$1" | tr '[:upper:]' '[:lower:]'
}

# Helper: capitalize first letter
capitalize() {
  local s="$1"
  if [[ -z "$s" ]]; then echo "$s"; return; fi
  local first="${s:0:1}"
  local rest="${s:1}"
  echo "$(echo "$first" | tr '[:lower:]' '[:upper:]')$rest"
}

categorize_and_add() {
  local raw="$1"

  # Skip merge commits (documented behavior)
  if [[ "$raw" == Merge\ * ]] || [[ "$raw" == "Merge pull request"* ]] || [[ "$raw" == "Merge branch"* ]]; then
    return 0
  fi

  local subject="$raw"
  local ctype=""
  local cleaned="$subject"

  # Parse conventional commit: type(scope)!: subject  or  type: subject
  local cc_regex='^([a-zA-Z]+)(\([^)]*\))?(!)?:[[:space:]](.+)$'
  if [[ "$subject" =~ $cc_regex ]]; then
    ctype="$(lowercase "${BASH_REMATCH[1]}")"
    cleaned="${BASH_REMATCH[4]}"
  else
    ctype=""
    cleaned="$subject"
  fi

  # Clean: trim leading spaces, capitalize first letter
  cleaned="$(echo "$cleaned" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
  cleaned="$(capitalize "$cleaned")"

  local lower_cleaned
  lower_cleaned="$(lowercase "$cleaned")"
  local lower_raw
  lower_raw="$(lowercase "$raw")"

  local category="Changed"

  # 1) Explicit conventional types
  case "$ctype" in
    feat|feature)
      category="Added"
      ;;
    fix|bugfix|hotfix)
      category="Fixed"
      ;;
    revert|remove|delete)
      category="Removed"
      ;;
    refactor|perf|style|chore|docs|test|build|ci|types)
      category="Changed"
      ;;
  esac

  # 2) Keyword heuristics override Changed → more specific when type absent or generic
  # Removed keywords take precedence over Changed
  if [[ "$category" == "Changed" ]]; then
    if echo "$lower_cleaned" | grep -Eq '\b(remove|removed|removes|delete|deleted|drop|dropped|deprecate|deprecated|eliminate|strip out)\b'; then
      category="Removed"
    elif echo "$lower_cleaned" | grep -Eq '\b(fix|fixes|fixed|bugfix|hotfix|patch|resolve|resolves|correct|repair)\b'; then
      # Only promote to Fixed if no explicit feat type
      if [[ "$ctype" != "feat" && "$ctype" != "feature" ]]; then
        category="Fixed"
      fi
    elif echo "$lower_cleaned" | grep -Eq '\b(add|adds|added|introduce|introduces|implement|implements|create|creates|new feature|support for)\b'; then
      if [[ -z "$ctype" ]]; then
        category="Added"
      fi
    fi
  fi

  # Removed keyword check even for feat/fix: a "feat: remove X" is Removed
  if echo "$lower_cleaned" | grep -Eq '^\s*(remove|delete|drop|deprecate)\b'; then
    category="Removed"
  fi

  case "$category" in
    Added)   ADDED+=("$cleaned") ;;
    Fixed)   FIXED+=("$cleaned") ;;
    Removed) REMOVED+=("$cleaned") ;;
    *)       CHANGED+=("$cleaned") ;;
  esac
}

for s in "${RAW_SUBJECTS[@]}"; do
  # Skip empty lines
  [[ -z "$s" ]] && continue
  categorize_and_add "$s"
done

TOTAL=$(( ${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} ))

# Write CHANGELOG.md (Keep a Changelog style)
{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project will be documented in this file."
  echo ""
  echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)."
  echo ""
  echo "## [$VERSION] - $DATE_STR"
  echo ""

  if [[ "$TOTAL" -eq 0 ]]; then
    echo "_No changes in this range ($RANGE_NOTE)._"
    echo ""
  else
    if [[ ${#ADDED[@]} -gt 0 ]]; then
      echo "### Added"
      echo ""
      for item in "${ADDED[@]}"; do echo "- $item"; done
      echo ""
    fi
    if [[ ${#FIXED[@]} -gt 0 ]]; then
      echo "### Fixed"
      echo ""
      for item in "${FIXED[@]}"; do echo "- $item"; done
      echo ""
    fi
    if [[ ${#CHANGED[@]} -gt 0 ]]; then
      echo "### Changed"
      echo ""
      for item in "${CHANGED[@]}"; do echo "- $item"; done
      echo ""
    fi
    if [[ ${#REMOVED[@]} -gt 0 ]]; then
      echo "### Removed"
      echo ""
      for item in "${REMOVED[@]}"; do echo "- $item"; done
      echo ""
    fi
  fi
} > "$OUTPUT"

echo "Wrote $OUTPUT ($TOTAL commits categorized: Added=${#ADDED[@]}, Fixed=${#FIXED[@]}, Changed=${#CHANGED[@]}, Removed=${#REMOVED[@]})" >&2
echo "$OUTPUT"
