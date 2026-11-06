#!/usr/bin/env bash
# ==============================================================================
# changelog.sh — Generate a structured CHANGELOG.md from Git History
# Bounty: claude-builders-bounty/claude-builders-bounty #1 ($50 USD)
# ==============================================================================
set -euo pipefail

OUTPUT_FILE="CHANGELOG.md"
VERSION_LABEL="Unreleased"
SINCE_REF=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output)
      OUTPUT_FILE="$2"
      shift 2
      ;;
    -v|--version)
      VERSION_LABEL="$2"
      shift 2
      ;;
    -s|--since)
      SINCE_REF="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: ./changelog.sh [--output CHANGELOG.md] [--version v1.2.0] [--since <tag>]"
      exit 0
      ;;
    *)
      shift
      ;;
  esac
done

if ! git rev-parse --git-dir > /dev/null 2>&1; then
  echo "Error: Current directory is not a git repository." >&2
  exit 1
fi

if [[ -z "$SINCE_REF" ]]; then
  if git describe --tags --abbrev=0 > /dev/null 2>&1; then
    SINCE_REF="$(git describe --tags --abbrev=0)"
  fi
fi

if [[ -n "$SINCE_REF" ]]; then
  RANGE="${SINCE_REF}..HEAD"
  RANGE_DESC="Changes since \`${SINCE_REF}\`"
else
  RANGE="HEAD"
  RANGE_DESC="All commits in repository"
fi

DATE_STR="$(date +%Y-%m-%d)"

ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
SECURITY=()

while IFS='|' read -r HASH SUBJECT AUTHOR; do
  [[ -z "$HASH" ]] && continue
  CLEAN_SUBJECT="$(echo "$SUBJECT" | sed -E 's/^[a-zA-Z]+(\([^)]+\))?!?:[[:space:]]*//')"
  ENTRY="- ${CLEAN_SUBJECT} (\`${HASH}\` by @${AUTHOR})"
  LOWER_SUBJ="$(echo "$SUBJECT" | tr '[:upper:]' '[:lower:]')"

  if [[ "$LOWER_SUBJ" =~ ^(sec|security|vuln) ]] || [[ "$LOWER_SUBJ" == *"security"* ]]; then
    SECURITY+=("$ENTRY")
  elif [[ "$LOWER_SUBJ" =~ ^(feat|add|new)(\([^)]+\))?!?: ]] || [[ "$LOWER_SUBJ" =~ ^(add|new|implement)[[:space:]] ]]; then
    ADDED+=("$ENTRY")
  elif [[ "$LOWER_SUBJ" =~ ^(fix|bug|hotfix|patch)(\([^)]+\))?!?: ]] || [[ "$LOWER_SUBJ" =~ ^(fix|resolve|patch)[[:space:]] ]]; then
    FIXED+=("$ENTRY")
  elif [[ "$LOWER_SUBJ" =~ ^(remove|delete|drop|deprecate)(\([^)]+\))?!?: ]] || [[ "$LOWER_SUBJ" =~ ^(remove|delete|drop)[[:space:]] ]]; then
    REMOVED+=("$ENTRY")
  else
    CHANGED+=("$ENTRY")
  fi
done < <(git log "$RANGE" --no-merges --pretty=format:"%h|%s|%an")

{
  echo "# Changelog"
  echo ""
  echo "All notable changes to this project are documented in this file."
  echo "Generated automatically from git history (${RANGE_DESC})."
  echo ""
  echo "## [${VERSION_LABEL}] - ${DATE_STR}"
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

  if [[ ${#SECURITY[@]} -gt 0 ]]; then
    echo "### Security"
    printf '%s\n' "${SECURITY[@]}"
    echo ""
  fi
} > "$OUTPUT_FILE"

echo "Successfully generated ${OUTPUT_FILE} (${RANGE_DESC})."
