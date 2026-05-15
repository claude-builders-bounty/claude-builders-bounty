#!/usr/bin/env bash
set -euo pipefail

# Generate a structured CHANGELOG.md from git history
# Usage: bash scripts/generate-changelog.sh [--dry-run] [--output FILE]

OUTPUT_FILE="CHANGELOG.md"
DRY_RUN=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --output)
      OUTPUT_FILE="$2"
      shift 2
      ;;
    -h|--help)
      cat <<HELP
Generate a structured CHANGELOG.md from git history.

Usage:
  bash scripts/generate-changelog.sh [options]

Options:
  --dry-run        Print changelog to stdout instead of writing file
  --output FILE    Write changelog to FILE (default: CHANGELOG.md)
  -h, --help       Show this help message

The script fetches commits since the last git tag and categorizes them into:
Added, Fixed, Changed, and Removed.
HELP
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: Not inside a git repository" >&2
  exit 1
fi

# Get latest tag. If none exists, use all commits.
LATEST_TAG=""
if LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null); then
  RANGE="${LATEST_TAG}..HEAD"
  RANGE_LABEL="since ${LATEST_TAG}"
else
  RANGE="HEAD"
  RANGE_LABEL="from project start (no git tags found)"
fi

# Get commits: hash + subject. Exclude merge commits for cleaner changelog.
COMMITS=$(git log --no-merges --pretty=format:'%h%x09%s' "$RANGE" 2>/dev/null || true)

TODAY=$(date +%Y-%m-%d)

# Use temp files to avoid bash array portability issues.
TMP_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_DIR"' EXIT
ADDED="$TMP_DIR/added"
FIXED="$TMP_DIR/fixed"
CHANGED="$TMP_DIR/changed"
REMOVED="$TMP_DIR/removed"
: > "$ADDED"
: > "$FIXED"
: > "$CHANGED"
: > "$REMOVED"

categorize_commit() {
  local subject="$1"
  local lower
  lower=$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')

  if printf '%s' "$lower" | grep -Eq '(^|[^a-z])(fix|fixed|bug|patch|resolve|resolved|correct|hotfix)([^a-z]|$)'; then
    echo "fixed"
  elif printf '%s' "$lower" | grep -Eq '(^|[^a-z])(remove|removed|delete|deleted|deprecate|deprecated|drop|dropped)([^a-z]|$)'; then
    echo "removed"
  elif printf '%s' "$lower" | grep -Eq '(^|[^a-z])(add|added|new|feature|feat|implement|implemented|introduce|introduced)([^a-z]|$)'; then
    echo "added"
  elif printf '%s' "$lower" | grep -Eq '(^|[^a-z])(change|changed|update|updated|refactor|refactored|improve|improved|modify|modified|enhance|enhanced)([^a-z]|$)'; then
    echo "changed"
  else
    echo "changed"
  fi
}

if [[ -n "$COMMITS" ]]; then
  while IFS=$'\t' read -r hash subject; do
    [[ -z "${subject:-}" ]] && continue
    entry="- ${subject} (${hash})"
    case "$(categorize_commit "$subject")" in
      added) echo "$entry" >> "$ADDED" ;;
      fixed) echo "$entry" >> "$FIXED" ;;
      removed) echo "$entry" >> "$REMOVED" ;;
      changed) echo "$entry" >> "$CHANGED" ;;
    esac
  done <<< "$COMMITS"
fi

append_section() {
  local title="$1"
  local file="$2"
  if [[ -s "$file" ]]; then
    printf '\n### %s\n\n' "$title"
    cat "$file"
  fi
}

CHANGELOG_CONTENT=$(
  cat <<HEADER
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased] - ${TODAY}

_Generated from git history ${RANGE_LABEL}._
HEADER

  if [[ -z "$COMMITS" ]]; then
    printf '\nNo commits found %s.\n' "$RANGE_LABEL"
  else
    append_section "Added" "$ADDED"
    append_section "Fixed" "$FIXED"
    append_section "Changed" "$CHANGED"
    append_section "Removed" "$REMOVED"
  fi
)

if [[ "$DRY_RUN" == true ]]; then
  printf '%s\n' "$CHANGELOG_CONTENT"
else
  printf '%s\n' "$CHANGELOG_CONTENT" > "$OUTPUT_FILE"
  echo "Generated ${OUTPUT_FILE} from git history ${RANGE_LABEL}."
fi
