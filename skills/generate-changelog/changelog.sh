#!/usr/bin/env bash
set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
REPO_NAME="$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")"
TODAY="$(date -u +"%Y-%m-%d")"

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "$LAST_TAG" ]]; then
  RANGE="${LAST_TAG}..HEAD"
  HEADER_LABEL="Unreleased (since ${LAST_TAG})"
else
  RANGE="HEAD"
  HEADER_LABEL="Unreleased (all commits)"
fi

ADDED=()
FIXED=()
CHANGED=()
REMOVED=()

while IFS='|' read -r hash subject date; do
  [[ -z "$hash" ]] && continue
  clean_subj="$(echo "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]+\))?!?:[[:space:]]*//')"
  entry="- ${clean_subj} (\`${hash}\`)"
  low="$(echo "$subject" | tr '[:upper:]' '[:lower:]')"

  if [[ "$low" =~ ^(feat|add|new|init|create) ]] || [[ "$low" =~ (add |added |new |implement|support) ]]; then
    ADDED+=("$entry")
  elif [[ "$low" =~ ^(fix|bug|hotfix|patch) ]] || [[ "$low" =~ (fix|fixed|resolve|bug|error|crash) ]]; then
    FIXED+=("$entry")
  elif [[ "$low" =~ ^(remove|del|drop|deprecate|clean) ]] || [[ "$low" =~ (remove|removed|delete|deleted|drop) ]]; then
    REMOVED+=("$entry")
  else
    CHANGED+=("$entry")
  fi
done < <(git log "$RANGE" --no-merges --pretty=format:"%h|%s|%cs" 2>/dev/null || true)

{
  echo "# Changelog — ${REPO_NAME}"
  echo ""
  echo "All notable changes to this project are documented in this file."
  echo ""
  echo "## [${HEADER_LABEL}] - ${TODAY}"
  echo ""

  echo "### Added"
  if [[ ${#ADDED[@]} -gt 0 ]]; then
    printf '%s\n' "${ADDED[@]}"
  else
    echo "- _No additions in this release._"
  fi
  echo ""

  echo "### Fixed"
  if [[ ${#FIXED[@]} -gt 0 ]]; then
    printf '%s\n' "${FIXED[@]}"
  else
    echo "- _No bug fixes in this release._"
  fi
  echo ""

  echo "### Changed"
  if [[ ${#CHANGED[@]} -gt 0 ]]; then
    printf '%s\n' "${CHANGED[@]}"
  else
    echo "- _No modifications in this release._"
  fi
  echo ""

  echo "### Removed"
  if [[ ${#REMOVED[@]} -gt 0 ]]; then
    printf '%s\n' "${REMOVED[@]}"
  else
    echo "- _No removals in this release._"
  fi
} > "$OUTPUT_FILE"

echo "Generated ${OUTPUT_FILE} (${HEADER_LABEL})"
