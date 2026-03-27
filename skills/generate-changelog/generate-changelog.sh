#!/usr/bin/env bash
set -euo pipefail

# generate-changelog.sh
# Generates a structured CHANGELOG entry from git history.
# Usage: ./generate-changelog.sh [--since <tag|date>] [--until <tag|date>]

SINCE=""
UNTIL="HEAD"
VERSION=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --since) SINCE="$2"; shift 2 ;;
    --until) UNTIL="$2"; shift 2 ;;
    --version) VERSION="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

# If no --since, use the most recent tag
if [[ -z "$SINCE" ]]; then
  SINCE=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

# Build the git log range
if [[ -n "$SINCE" ]]; then
  RANGE="${SINCE}..${UNTIL}"
else
  RANGE="$UNTIL"
fi

# Determine version header
if [[ -n "$VERSION" ]]; then
  HEADER="$VERSION"
elif [[ "$UNTIL" != "HEAD" ]]; then
  HEADER="$UNTIL"
else
  HEADER="Unreleased ($(date +%Y-%m-%d))"
fi

# Collect commits, skip merge commits
COMMITS=$(git log "$RANGE" --pretty=format:"%s|||%h|||%an" --no-merges 2>/dev/null || echo "")

if [[ -z "$COMMITS" ]]; then
  echo "No commits found in range ${RANGE}"
  exit 0
fi

# Category arrays
declare -a ADDED=() FIXED=() CHANGED=() DOCS=() TESTS=() MAINTENANCE=() BREAKING=() OTHER=()

while IFS= read -r line; do
  msg=$(echo "$line" | cut -d'|' -f1)
  hash=$(echo "$line" | cut -d'|' -f4)
  author=$(echo "$line" | cut -d'|' -f7)

  # Strip scope: "feat(api): blah" -> "blah"
  clean_msg=$(echo "$msg" | sed -E 's/^[a-z]+(\([^)]*\))?[!]?:\s*//')
  entry="- ${clean_msg} (\`${hash}\`)"

  # Check for breaking change indicator
  if echo "$msg" | grep -qiE '^(breaking|feat!|fix!|refactor!)' || echo "$msg" | grep -q 'BREAKING CHANGE'; then
    BREAKING+=("$entry")
  fi

  case "$msg" in
    feat*|add*|new*)       ADDED+=("$entry") ;;
    fix*|bug*|patch*)      FIXED+=("$entry") ;;
    refactor*|perf*|opt*)  CHANGED+=("$entry") ;;
    docs*|doc:*)           DOCS+=("$entry") ;;
    test*)                 TESTS+=("$entry") ;;
    chore*|ci*|build*|dep*) MAINTENANCE+=("$entry") ;;
    *)                     OTHER+=("$entry") ;;
  esac
done <<< "$COMMITS"

# Output
echo "## ${HEADER}"
echo ""

print_section() {
  local title="$1"
  shift
  local items=("$@")
  if [[ ${#items[@]} -gt 0 ]]; then
    echo "### ${title}"
    printf '%s\n' "${items[@]}"
    echo ""
  fi
}

print_section "Breaking Changes" "${BREAKING[@]}"
print_section "Added" "${ADDED[@]}"
print_section "Fixed" "${FIXED[@]}"
print_section "Changed" "${CHANGED[@]}"
print_section "Documentation" "${DOCS[@]}"
print_section "Tests" "${TESTS[@]}"
print_section "Maintenance" "${MAINTENANCE[@]}"
print_section "Other" "${OTHER[@]}"
