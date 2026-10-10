#!/usr/bin/env bash
set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
  echo "Error: run this command inside a Git repository." >&2
  exit 1
}

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"

if [ -n "$LAST_TAG" ]; then
  RANGE="${LAST_TAG}..HEAD"
  SINCE="since ${LAST_TAG}"
else
  RANGE="HEAD"
  SINCE="from repository start"
fi

COMMITS="$(git log "$RANGE" --no-merges --pretty=format:'%s' 2>/dev/null || true)"

declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()

while IFS= read -r msg; do
  [ -z "$msg" ] && continue

  lower="$(printf '%s' "$msg" | tr '[:upper:]' '[:lower:]')"

  case "$lower" in
    feat:*|feat\(*|add:*|added:*|new:*)
      ADDED+=("$msg")
      ;;
    fix:*|fix\(*|bugfix:*|hotfix:*)
      FIXED+=("$msg")
      ;;
    remove:*|removed:*|delete:*|deleted:*)
      REMOVED+=("$msg")
      ;;
    *)
      CHANGED+=("$msg")
      ;;
  esac
done <<< "$COMMITS"

{
  echo "# Changelog"
  echo
  echo "Generated from Git history ${SINCE}."
  echo

  for section in Added Fixed Changed Removed; do
    echo "## $section"
    echo

    case "$section" in
      Added)   items=("${ADDED[@]+"${ADDED[@]}"}") ;;
      Fixed)   items=("${FIXED[@]+"${FIXED[@]}"}") ;;
      Changed) items=("${CHANGED[@]+"${CHANGED[@]}"}") ;;
      Removed) items=("${REMOVED[@]+"${REMOVED[@]}"}") ;;
    esac

    if [ "${#items[@]}" -eq 0 ]; then
      echo "- Nothing to report."
    else
      printf -- '- %s\n' "${items[@]}"
    fi
    echo
  done
} > "$OUTPUT"

echo "Generated $OUTPUT"
