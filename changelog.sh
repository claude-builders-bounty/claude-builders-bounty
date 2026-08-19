#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: ./changelog.sh [repo-path]
#   If repo-path is omitted, uses the current directory.
# Falls back to SKILL.md behavior when invoked via Claude Code `/generate-changelog`.

set -euo pipefail

REPO_DIR="${1:-.}"
CHANGELOG="${REPO_DIR}/CHANGELOG.md"
HEADER="# Changelog\n"

# --- Detect last tag ---
LAST_TAG=$(git -C "$REPO_DIR" describe --tags --abbrev=0 2>/dev/null || echo "")

if [ -z "$LAST_TAG" ]; then
  # No tags — use the root commit
  RANGE=$(git -C "$REPO_DIR" rev-list --max-parents=0 HEAD 2>/dev/null)
  if [ -z "$RANGE" ]; then
    echo "No commits found." >&2
    exit 1
  fi
  LOG_RANGE="${RANGE}..HEAD"
else
  LOG_RANGE="${LAST_TAG}..HEAD"
fi

# --- Fetch commits ---
COMMITS=$(git -C "$REPO_DIR" log $LOG_RANGE --pretty=format:"%s|%b" --no-merges 2>/dev/null)

if [ -z "$COMMITS" ]; then
  echo "No new commits since ${LAST_TAG:-the beginning}." >&2
  exit 0
fi

# --- Date ---
TODAY=$(date +%Y-%m-%d)

# --- Categorize ---
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
SECURITY=""
DOCS=""
BREAKING=""

categorize() {
  local subject="$1"
  local body="$2"
  local lower
  lower=$(echo "$subject" | tr '[:upper:]' '[:lower:]')

  # Check breaking changes
  if echo "${subject}\n${body}" | grep -qiE 'BREAKING[ -]CHANGE:|BREAKING:'; then
    local desc
    desc=$(echo "$body" | grep -iE 'BREAKING[ -]CHANGE:|BREAKING:' | sed 's/BREAKING[ -]CHANGE://I;s/BREAKING://I' | sed 's/^[[:space:]]*//' | head -1)
    if [ -z "$desc" ]; then
      desc="$subject"
    fi
    BREAKING="${BREAKING}- ${desc}\n"
  fi

  # Link issue numbers
  local linked_subject
  linked_subject=$(echo "$subject" | sed -E 's/#([0-9]+)/[#\1](\.\.\/issues\/\1)/g')

  # Categorize by prefix/keyword
  if echo "$lower" | grep -qE '^(feat|add|new|introduce|implement)[:(/]|\b(adds?|new|introduc|implement)\b'; then
    ADDED="${ADDED}- ${linked_subject}\n"
  elif echo "$lower" | grep -qE '^(fix|bug|patch|resolve|repair)[:(/]|\b(fix|bug|patch|resolv|repair)\b'; then
    FIXED="${FIXED}- ${linked_subject}\n"
  elif echo "$lower" | grep -qE '^(remove|delete|drop|deprecate|revert)[:(/]|\b(remov|delet|drop|deprecat|revert)\b'; then
    REMOVED="${REMOVED}- ${linked_subject}\n"
  elif echo "$lower" | grep -qE '^(security|vuln|cve|xss|injection)[:(/]|\b(security|vuln|cve|xss|injection)\b'; then
    SECURITY="${SECURITY}- ${linked_subject}\n"
  elif echo "$lower" | grep -qE '^(docs|documentation|readme|comment)[:(/]|\b(doc|readme|comment)\b'; then
    DOCS="${DOCS}- ${linked_subject}\n"
  else
    CHANGED="${CHANGED}- ${linked_subject}\n"
  fi
}

# Process each commit
while IFS='|' read -r subject body; do
  [ -z "$subject" ] && continue
  categorize "$subject" "$body"
done <<< "$COMMITS"

# --- Build output ---
OUTPUT="## [Unreleased] - ${TODAY}\n\n"

if [ -n "$BREAKING" ]; then
  OUTPUT="${OUTPUT}### Breaking Changes\n${BREAKING}\n"
fi
if [ -n "$ADDED" ]; then
  OUTPUT="${OUTPUT}### Added\n${ADDED}\n"
fi
if [ -n "$FIXED" ]; then
  OUTPUT="${OUTPUT}### Fixed\n${FIXED}\n"
fi
if [ -n "$CHANGED" ]; then
  OUTPUT="${OUTPUT}### Changed\n${CHANGED}\n"
fi
if [ -n "$REMOVED" ]; then
  OUTPUT="${OUTPUT}### Removed\n${REMOVED}\n"
fi
if [ -n "$SECURITY" ]; then
  OUTPUT="${OUTPUT}### Security\n${SECURITY}\n"
fi
if [ -n "$DOCS" ]; then
  OUTPUT="${OUTPUT}### Docs\n${DOCS}\n"
fi

# --- Write ---
if [ -f "$CHANGELOG" ]; then
  # Insert new entries after the header line
  # Find the first blank line after the header and insert before existing content
  TEMP=$(mktemp)
  {
    echo -e "$HEADER"
    echo -e "$OUTPUT"
    # Skip the existing header (# Changelog) and any existing Unreleased section
    awk 'NR==1 && /^# Changelog/{next} /^## \[Unreleased\]/{found=1; next} found && /^## \[/{found=0} !found' "$CHANGELOG"
  } > "$TEMP"
  mv "$TEMP" "$CHANGELOG"
else
  echo -e "${HEADER}${OUTPUT}" > "$CHANGELOG"
fi

echo "CHANGELOG.md updated with commits since ${LAST_TAG:-the beginning}."
echo "Sections: Added=$(echo -e "$ADDED" | grep -c '^-' || true), Fixed=$(echo -e "$FIXED" | grep -c '^-' || true), Changed=$(echo -e "$CHANGED" | grep -c '^-' || true), Removed=$(echo -e "$REMOVED" | grep -c '^-' || true), Security=$(echo -e "$SECURITY" | grep -c '^-' || true), Docs=$(echo -e "$DOCS" | grep -c '^-' || true)"
