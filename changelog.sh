#!/usr/bin/env bash
#
# changelog.sh — Generate a structured CHANGELOG.md from git history.
# Fulfills acceptance criteria for Claude Code skill and standalone CLI.
#
# Usage:
#   bash changelog.sh [options]
#
# Options:
#   --from <ref>     Starting tag or commit (default: most recent git tag, or initial commit)
#   --to <ref>       Ending tag or commit (default: HEAD)
#   --output <file>  Output file path (default: CHANGELOG.md)
#   --stdout         Print output to stdout instead of writing to file
#   -h, --help       Show this help message
#

set -euo pipefail

FROM_REF=""
TO_REF="HEAD"
OUTPUT_FILE="CHANGELOG.md"
TO_STDOUT=0

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --from)
      FROM_REF="$2"
      shift 2
      ;;
    --to)
      TO_REF="$2"
      shift 2
      ;;
    --output)
      OUTPUT_FILE="$2"
      shift 2
      ;;
    --stdout)
      TO_STDOUT=1
      shift
      ;;
    -h|--help)
      echo "Usage: bash changelog.sh [--from <ref>] [--to <ref>] [--output <file>] [--stdout]"
      echo ""
      echo "Generate a Keep-A-Changelog compatible CHANGELOG.md from git history."
      echo "Automatically categorizes commits into: Added, Fixed, Changed, Removed."
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

# Resolve starting reference if not explicitly passed
if [[ -z "$FROM_REF" ]]; then
  # Try to find the latest git tag before TO_REF
  LATEST_TAG=$(git describe --tags --abbrev=0 "${TO_REF}^" 2>/dev/null || git describe --tags --abbrev=0 "${TO_REF}" 2>/dev/null || true)
  if [[ -n "$LATEST_TAG" ]]; then
    FROM_REF="$LATEST_TAG"
  else
    # Fallback to the root/initial commit
    FROM_REF=$(git rev-list --max-parents=0 "${TO_REF}" 2>/dev/null | tail -n 1 || true)
  fi
fi

# Build revision range
if [[ -n "$FROM_REF" && "$FROM_REF" != "$TO_REF" ]]; then
  REV_RANGE="${FROM_REF}..${TO_REF}"
  RANGE_LABEL="[Unreleased] (${FROM_REF}..${TO_REF})"
else
  REV_RANGE="${TO_REF}"
  RANGE_LABEL="[Unreleased]"
fi

TODAY=$(date +%Y-%m-%d 2>/dev/null || date -u +%Y-%m-%d)

# Temporary arrays / accumulators
ADDED_ENTRIES=()
FIXED_ENTRIES=()
CHANGED_ENTRIES=()
REMOVED_ENTRIES=()

# Read commit history
while IFS='|' read -r hash subject author; do
  [[ -z "$subject" ]] && continue

  # Categorization heuristics
  lower_subject=$(echo "$subject" | tr '[:upper:]' '[:lower:]')
  entry="- ${subject} ([${hash:0:7}])"

  if [[ "$lower_subject" =~ ^(feat|add|new|feature) ]]; then
    ADDED_ENTRIES+=("$entry")
  elif [[ "$lower_subject" =~ ^(fix|bug|patch|resolve|close) ]]; then
    FIXED_ENTRIES+=("$entry")
  elif [[ "$lower_subject" =~ ^(remove|delete|deprecat|drop) ]]; then
    REMOVED_ENTRIES+=("$entry")
  else
    # Default to Changed for refactor, docs, chore, style, perf, etc.
    CHANGED_ENTRIES+=("$entry")
  fi
done < <(git log "${REV_RANGE}" --pretty=format:"%h|%s|%an" 2>/dev/null || true)

# Build formatted Markdown content
CHANGELOG_CONTENT="# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## ${RANGE_LABEL} - ${TODAY}
"

if [[ ${#ADDED_ENTRIES[@]} -gt 0 ]]; then
  CHANGELOG_CONTENT+=$'\n### Added\n'
  for item in "${ADDED_ENTRIES[@]}"; do
    CHANGELOG_CONTENT+="${item}"$'\n'
  done
fi

if [[ ${#FIXED_ENTRIES[@]} -gt 0 ]]; then
  CHANGELOG_CONTENT+=$'\n### Fixed\n'
  for item in "${FIXED_ENTRIES[@]}"; do
    CHANGELOG_CONTENT+="${item}"$'\n'
  done
fi

if [[ ${#CHANGED_ENTRIES[@]} -gt 0 ]]; then
  CHANGELOG_CONTENT+=$'\n### Changed\n'
  for item in "${CHANGED_ENTRIES[@]}"; do
    CHANGELOG_CONTENT+="${item}"$'\n'
  done
fi

if [[ ${#REMOVED_ENTRIES[@]} -gt 0 ]]; then
  CHANGELOG_CONTENT+=$'\n### Removed\n'
  for item in "${REMOVED_ENTRIES[@]}"; do
    CHANGELOG_CONTENT+="${item}"$'\n'
  done
fi

if [[ ${#ADDED_ENTRIES[@]} -eq 0 && ${#FIXED_ENTRIES[@]} -eq 0 && ${#CHANGED_ENTRIES[@]} -eq 0 && ${#REMOVED_ENTRIES[@]} -eq 0 ]]; then
  CHANGELOG_CONTENT+=$'\n*No notable commits found in the specified range.*\n'
fi

# Output handling
if [[ "$TO_STDOUT" -eq 1 ]]; then
  echo "$CHANGELOG_CONTENT"
else
  echo "$CHANGELOG_CONTENT" > "$OUTPUT_FILE"
  echo "✅ Successfully generated changelog at: $OUTPUT_FILE"
fi
