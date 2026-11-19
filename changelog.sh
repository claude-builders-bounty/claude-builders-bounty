#!/usr/bin/env bash
# changelog.sh — generate a structured CHANGELOG.md from git history
# Usage:
#   bash changelog.sh                 # write ./CHANGELOG.md
#   bash changelog.sh /path/to/repo   # write <repo>/CHANGELOG.md
#   bash changelog.sh --stdout        # print to stdout only
set -euo pipefail

ROOT="${1:-.}"
WRITE=1
if [ "${1:-}" = "--stdout" ]; then
  ROOT="."
  WRITE=0
fi

if ! git -C "$ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  echo "error: not inside a git repository: $ROOT" >&2
  exit 1
fi

cd "$ROOT"

# Find the newest tag (respects annotated tags and semver sort)
LAST_TAG=""
if LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null); then
  RANGE="${LAST_TAG}..HEAD"
else
  RANGE="HEAD"
fi

mapfile -t COMMITS < <(git log --no-merges --pretty=format:'%s' "$RANGE" 2>/dev/null || true)

# Categorize subjects into buckets (everything else lands in Changed)
ADDED=(); FIXED=(); CHANGED=(); REMOVED=()
for line in "${COMMITS[@]:-}"; do
  [ -n "${line// /}" ] || continue
  lower=$(printf '%s' "$line" | tr '[:upper:]' '[:lower:]')
  case "$lower" in
    feat*|add*|new*|create*|implement*|introduce*|support*) ADDED+=("$line");;
    fix*|bug*|patch*|correct*|repair*|hotfix*|resolve*)    FIXED+=("$line");;
    remove*|delete*|drop*|retire*|deprecate*)                REMOVED+=("$line");;
    *)                                                        CHANGED+=("$line");;
  esac
done

{
  echo "# Changelog"
  echo
  echo "Generated from \`git log ${RANGE}\` on $(date -u +%Y-%m-%dT%H:%M:%SZ)."
  echo
  echo "## [Unreleased]"
  echo
  echo "### Added"
  if [ ${#ADDED[@]} -gt 0 ]; then
    for c in "${ADDED[@]}"; do echo "- $c"; done
  else
    echo "- (none)"
  fi
  echo
  echo "### Changed"
  if [ ${#CHANGED[@]} -gt 0 ]; then
    for c in "${CHANGED[@]}"; do echo "- $c"; done
  else
    echo "- (none)"
  fi
  echo
  echo "### Fixed"
  if [ ${#FIXED[@]} -gt 0 ]; then
    for c in "${FIXED[@]}"; do echo "- $c"; done
  else
    echo "- (none)"
  fi
  echo
  echo "### Removed"
  if [ ${#REMOVED[@]} -gt 0 ]; then
    for c in "${REMOVED[@]}"; do echo "- $c"; done
  else
    echo "- (none)"
  fi
} > /tmp/changelog-gen.md

if [ "$WRITE" = "1" ]; then
  cp /tmp/changelog-gen.md "$ROOT/CHANGELOG.md"
  echo "Wrote $ROOT/CHANGELOG.md"
else
  cat /tmp/changelog-gen.md
fi
