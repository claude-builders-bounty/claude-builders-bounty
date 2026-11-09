#!/usr/bin/env bash
# Generate CHANGELOG.md from commits since the last git tag.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${ROOT}" ]]; then
  echo "error: not inside a git repository" >&2
  exit 1
fi
cd "$ROOT"

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "${LAST_TAG}" ]]; then
  RANGE_ARGS=("${LAST_TAG}..HEAD")
  SINCE_LABEL="since ${LAST_TAG}"
else
  RANGE_ARGS=("HEAD")
  SINCE_LABEL="full history (no tags)"
fi

TODAY="$(date -u +%Y-%m-%d)"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

if [[ -n "${LAST_TAG}" ]]; then
  git log "${LAST_TAG}..HEAD" --pretty=format:'%s' > "$TMP" || true
else
  git log HEAD --pretty=format:'%s' > "$TMP" || true
fi

ADDED=()
FIXED=()
CHANGED=()
REMOVED=()

while IFS= read -r subject || [[ -n "$subject" ]]; do
  [[ -z "$subject" ]] && continue
  body="$subject"
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  catg=Changed
  if [[ "$lower" =~ ^feat(\(.*\))?(!)?: ]]; then catg=Added
  elif [[ "$lower" =~ ^fix(\(.*\))?(!)?: ]]; then catg=Fixed
  elif [[ "$lower" =~ ^(remove|revert)(\(.*\))?(!)?: ]]; then catg=Removed
  elif [[ "$lower" =~ ^(chore|refactor|perf|docs|style|test|ci|build)(\(.*\))?(!)?: ]]; then catg=Changed
  elif [[ "$lower" =~ (^|[^a-z])(add|added|introduce|introduced|create|created|implement|implemented)([^a-z]|$) ]]; then catg=Added
  elif [[ "$lower" =~ (^|[^a-z])(fix|fixed|bug|hotfix|patch|resolve|resolved)([^a-z]|$) ]]; then catg=Fixed
  elif [[ "$lower" =~ (^|[^a-z])(remove|removed|delete|deleted|drop|dropped|deprecate|deprecated)([^a-z]|$) ]]; then catg=Removed
  fi
  case "$catg" in
    Added) ADDED+=("- ${body}") ;;
    Fixed) FIXED+=("- ${body}") ;;
    Removed) REMOVED+=("- ${body}") ;;
    *) CHANGED+=("- ${body}") ;;
  esac
done < "$TMP"

{
  echo "# Changelog"
  echo
  echo "## Unreleased (${TODAY})"
  echo
  echo "_Generated ${SINCE_LABEL}_"
  echo
  echo "### Added"
  if ((${#ADDED[@]})); then printf '%s\n' "${ADDED[@]}"; else echo "- (none)"; fi
  echo
  echo "### Fixed"
  if ((${#FIXED[@]})); then printf '%s\n' "${FIXED[@]}"; else echo "- (none)"; fi
  echo
  echo "### Changed"
  if ((${#CHANGED[@]})); then printf '%s\n' "${CHANGED[@]}"; else echo "- (none)"; fi
  echo
  echo "### Removed"
  if ((${#REMOVED[@]})); then printf '%s\n' "${REMOVED[@]}"; else echo "- (none)"; fi
  echo
} > CHANGELOG.md

echo "Wrote ${ROOT}/CHANGELOG.md (${SINCE_LABEL})"
