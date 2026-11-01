#!/usr/bin/env bash
# Standalone Keep a Changelog Generator from Git History (#1)
# Usage: ./changelog.sh [--version v1.0.0] [--output CHANGELOG.md] [--since <tag>]

set -euo pipefail

TARGET_VERSION="${1:-Unreleased}"
OUTPUT_FILE="CHANGELOG.md"
SINCE_TAG=""

# Parse optional flags
while [[ $# -gt 0 ]]; do
  case "$1" in
    --version|-v)
      TARGET_VERSION="$2"
      shift 2
      ;;
    --output|-o)
      OUTPUT_FILE="$2"
      shift 2
      ;;
    --since|-s)
      SINCE_TAG="$2"
      shift 2
      ;;
    *)
      TARGET_VERSION="$1"
      shift 1
      ;;
  esac
done

# 1. Determine base git tag
if [ -z "$SINCE_TAG" ]; then
  if git describe --tags --abbrev=0 >/dev/null 2>&1; then
    SINCE_TAG="$(git describe --tags --abbrev=0)"
    RANGE="${SINCE_TAG}..HEAD"
    echo "🔍 Fetching commits since latest tag: ${SINCE_TAG}"
  else
    RANGE="HEAD"
    echo "🔍 No tags found; fetching all commits in repository history"
  fi
else
  RANGE="${SINCE_TAG}..HEAD"
  echo "🔍 Fetching commits since specified tag: ${SINCE_TAG}"
fi

CURRENT_DATE="$(date +%Y-%m-%d)"
TEMP_LOG="$(mktemp)"

# Collect commits: hash, message, author
git log "$RANGE" --pretty=format:"%h%x09%s%x09%an" > "$TEMP_LOG"

ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
SECURITY=()

while IFS=$'\t' read -r hash subject author; do
  [ -z "$subject" ] && continue
  
  # Categorization regex matching
  lower_subj="$(echo "$subject" | tr '[:upper:]' '[:lower:]')"
  
  if [[ "$lower_subj" =~ ^(sec|security)(\(.*\))?: ]] || [[ "$lower_subj" =~ (vulnerability|cve|sanitize) ]]; then
    SECURITY+=("- ${subject} (${hash})")
  elif [[ "$lower_subj" =~ ^feat(\(.*\))?: ]] || [[ "$lower_subj" =~ ^(add|implement|support) ]]; then
    ADDED+=("- ${subject} (${hash})")
  elif [[ "$lower_subj" =~ ^fix(\(.*\))?: ]] || [[ "$lower_subj" =~ ^(bug|patch|resolve|close) ]]; then
    FIXED+=("- ${subject} (${hash})")
  elif [[ "$lower_subj" =~ ^(remove|delete|deprecate|drop) ]]; then
    REMOVED+=("- ${subject} (${hash})")
  else
    CHANGED+=("- ${subject} (${hash})")
  fi
done < "$TEMP_LOG"
rm -f "$TEMP_LOG"

# Build Markdown release section
NEW_SECTION="$(cat <<EOF
## [${TARGET_VERSION}] - ${CURRENT_DATE}

EOF
)"

if [ ${#ADDED[@]} -gt 0 ]; then
  NEW_SECTION="${NEW_SECTION}
### Added
$(printf '%s\n' "${ADDED[@]}")
"
fi

if [ ${#FIXED[@]} -gt 0 ]; then
  NEW_SECTION="${NEW_SECTION}
### Fixed
$(printf '%s\n' "${FIXED[@]}")
"
fi

if [ ${#CHANGED[@]} -gt 0 ]; then
  NEW_SECTION="${NEW_SECTION}
### Changed
$(printf '%s\n' "${CHANGED[@]}")
"
fi

if [ ${#REMOVED[@]} -gt 0 ]; then
  NEW_SECTION="${NEW_SECTION}
### Removed
$(printf '%s\n' "${REMOVED[@]}")
"
fi

if [ ${#SECURITY[@]} -gt 0 ]; then
  NEW_SECTION="${NEW_SECTION}
### Security
$(printf '%s\n' "${SECURITY[@]}")
"
fi

# Write or prepend to CHANGELOG.md
HEADER="$(cat <<'EOF'
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

EOF
)"

if [ ! -f "$OUTPUT_FILE" ]; then
  echo -e "${HEADER}\n${NEW_SECTION}" > "$OUTPUT_FILE"
  echo "✅ Generated new ${OUTPUT_FILE} with version [${TARGET_VERSION}]"
else
  # Prepend beneath header
  EXISTING_CONTENT="$(cat "$OUTPUT_FILE")"
  if grep -q "# Changelog" "$OUTPUT_FILE"; then
    # Keep header and insert below
    echo -e "${HEADER}\n${NEW_SECTION}\n$(grep -v "# Changelog" "$OUTPUT_FILE" | grep -v "All notable changes to this project" | grep -v "The format is based on" | grep -v "and this project adheres to")" > "$OUTPUT_FILE"
  else
    echo -e "${HEADER}\n${NEW_SECTION}\n${EXISTING_CONTENT}" > "$OUTPUT_FILE"
  fi
  echo "✅ Prepended release [${TARGET_VERSION}] to existing ${OUTPUT_FILE}"
fi
