#!/usr/bin/env bash
# Generate CHANGELOG.md from git history since the last tag.
set -euo pipefail

ROOT="${1:-.}"
OUT="${2:-CHANGELOG.md}"
cd "$ROOT"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "error: not a git repository" >&2
  exit 1
fi

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$LAST_TAG" ]; then
  RANGE="${LAST_TAG}..HEAD"
  SINCE_LINE="Changes since ${LAST_TAG}"
else
  RANGE="HEAD"
  SINCE_LINE="Initial changelog"
fi

added=()
fixed=()
changed=()
removed=()

while IFS= read -r line; do
  [ -z "$line" ] && continue
  subject="${line#*: }"
  lower="$(echo "$subject" | tr '[:upper:]' '[:lower:]')"
  case "$lower" in
    fix*|bug*|patch*) fixed+=("$subject") ;;
    remove*|delete*|drop*) removed+=("$subject") ;;
    change*|update*|refactor*|chore*|docs*) changed+=("$subject") ;;
    *) added+=("$subject") ;;
  esac
done < <(git log "$RANGE" --pretty=format:'%h: %s' 2>/dev/null || git log --pretty=format:'%h: %s')

DATE="$(date -u +%Y-%m-%d)"
VERSION="${LAST_TAG:-Unreleased}"

{
  echo "# Changelog"
  echo
  echo "## ${VERSION} (${DATE})"
  echo
  echo "${SINCE_LINE}"
  echo
  if [ ${#added[@]} -gt 0 ]; then
    echo "### Added"
    for item in "${added[@]}"; do echo "- ${item}"; done
    echo
  fi
  if [ ${#fixed[@]} -gt 0 ]; then
    echo "### Fixed"
    for item in "${fixed[@]}"; do echo "- ${item}"; done
    echo
  fi
  if [ ${#changed[@]} -gt 0 ]; then
    echo "### Changed"
    for item in "${changed[@]}"; do echo "- ${item}"; done
    echo
  fi
  if [ ${#removed[@]} -gt 0 ]; then
    echo "### Removed"
    for item in "${removed[@]}"; do echo "- ${item}"; done
    echo
  fi
} > "$OUT"

echo "Wrote ${OUT}"
