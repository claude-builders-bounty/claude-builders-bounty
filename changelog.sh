#!/usr/bin/env bash
set -euo pipefail

VERSION=""
FROM_REF=""
DATE=$(date +%Y-%m-%d)

while [[ $# -gt 0 ]]; do
  case $1 in
    --tag|--version)
      VERSION="$2"; FROM_REF="$2"; shift 2 ;;
    --from)
      FROM_REF="$2"; shift 2 ;;
    *)
      echo "Usage: $0 [--tag <tag>] [--from <ref>]"
      exit 1 ;;
  esac
done

if [ -z "$FROM_REF" ]; then
  LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
  if [ -n "$LAST_TAG" ]; then
    FROM_REF="$LAST_TAG"
    VERSION="${VERSION:-$LAST_TAG}"
  else
    FROM_REF=$(git rev-list --max-parents=0 HEAD 2>/dev/null || echo "")
    if [ -z "$FROM_REF" ]; then
      echo "Error: not a git repository or no commits found" >&2
      exit 1
    fi
    VERSION="${VERSION:-Unreleased}"
  fi
fi

VERSION="${VERSION:-Unreleased}"

LOG_RANGE="${FROM_REF}..HEAD"
if ! git rev-parse --verify "$FROM_REF" >/dev/null 2>&1; then
  echo "Error: ref '$FROM_REF' not found" >&2
  exit 1
fi

COMMITS=$(git log --oneline "$LOG_RANGE" 2>/dev/null || git log --oneline)

ADDED=()
FIXED=()
CHANGED=()
REMOVED=()

while IFS= read -r line; do
  msg=$(echo "$line" | sed 's/^[0-9a-f]\{7,40\} //')
  case "$msg" in
    feat:*|feature:*)
      body="${msg#*: }"; [ -n "$body" ] && ADDED+=("$body") ;;
    fix:*|bugfix:*)
      body="${msg#*: }"; [ -n "$body" ] && FIXED+=("$body") ;;
    refactor:*)
      body="${msg#*: }"; [ -n "$body" ] && CHANGED+=("$body") ;;
    remove:*|deprecate:*|delete:*)
      body="${msg#*: }"; [ -n "$body" ] && REMOVED+=("$body") ;;
    chore:*|docs:*|test:*)
      ;;
    *)
      CHANGED+=("$msg") ;;
  esac
done <<< "$COMMITS"

cat > CHANGELOG.md << EOF
# Changelog

## [${VERSION}] - ${DATE}

EOF

if [ ${#ADDED[@]} -gt 0 ]; then
  cat >> CHANGELOG.md << EOF
### Added
EOF
  for item in "${ADDED[@]}"; do
    echo "- ${item}" >> CHANGELOG.md
  done
  echo "" >> CHANGELOG.md
fi

if [ ${#FIXED[@]} -gt 0 ]; then
  cat >> CHANGELOG.md << EOF
### Fixed
EOF
  for item in "${FIXED[@]}"; do
    echo "- ${item}" >> CHANGELOG.md
  done
  echo "" >> CHANGELOG.md
fi

if [ ${#CHANGED[@]} -gt 0 ]; then
  cat >> CHANGELOG.md << EOF
### Changed
EOF
  for item in "${CHANGED[@]}"; do
    echo "- ${item}" >> CHANGELOG.md
  done
  echo "" >> CHANGELOG.md
fi

if [ ${#REMOVED[@]} -gt 0 ]; then
  cat >> CHANGELOG.md << EOF
### Removed
EOF
  for item in "${REMOVED[@]}"; do
    echo "- ${item}" >> CHANGELOG.md
  done
  echo "" >> CHANGELOG.md
fi

if [ ${#ADDED[@]} -eq 0 ] && [ ${#FIXED[@]} -eq 0 ] && [ ${#CHANGED[@]} -eq 0 ] && [ ${#REMOVED[@]} -eq 0 ]; then
  echo "_No changes since ${FROM_REF}_" >> CHANGELOG.md
fi

echo "Generated CHANGELOG.md from ${LOG_RANGE}"
