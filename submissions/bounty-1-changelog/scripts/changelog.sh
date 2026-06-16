#!/usr/bin/env bash
# Generate CHANGELOG.md from git history since the last tag.
# Usage: changelog.sh [output-file] [repo-path]
set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
REPO="${2:-.}"

cd "$REPO"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: not a git repository: $REPO" >&2
  exit 1
fi

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
RANGE=""
if [[ -n "$LAST_TAG" ]]; then
  RANGE="${LAST_TAG}..HEAD"
  SINCE_LINE="Changes since ${LAST_TAG}"
else
  SINCE_LINE="Initial changelog (no prior tags)"
fi

COMMITS=()
while IFS= read -r line; do
  [[ -n "$line" ]] && COMMITS+=("$line")
done < <(git log ${RANGE} --pretty=format:'%h|%s|%an|%ad' --date=short --no-merges)

ADDED=()
FIXED=()
CHANGED=()
REMOVED=()

categorize() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  if [[ "$lower" =~ ^(feat|feature|add|added|new)(\(|\:|$) ]] || [[ "$lower" =~ ^(add|added|new): ]]; then
    echo "added"
  elif [[ "$lower" =~ ^(fix|bugfix|hotfix|patch)(\(|\:|$) ]] || [[ "$lower" =~ ^fix: ]]; then
    echo "fixed"
  elif [[ "$lower" =~ ^(remove|removed|delete|deleted|drop|dropped)(\(|\:|$) ]] || [[ "$lower" =~ ^(remove|removed|delete|deleted): ]]; then
    echo "removed"
  elif [[ "$lower" =~ ^(refactor|change|changed|chore|style|perf|docs|build|ci|test)(\(|\:|$) ]]; then
    echo "changed"
  elif [[ "$lower" =~ remove|delete|drop ]]; then
    echo "removed"
  elif [[ "$lower" =~ fix|bug|patch|resolve ]]; then
    echo "fixed"
  elif [[ "$lower" =~ add|introduce|implement|support ]]; then
    echo "added"
  else
    echo "changed"
  fi
}

for entry in "${COMMITS[@]}"; do
  IFS='|' read -r hash subject author date <<<"$entry"
  [[ -z "$hash" ]] && continue
  line="- ${subject} (${hash}, ${date})"
  case "$(categorize "$subject")" in
    added) ADDED+=("$line") ;;
    fixed) FIXED+=("$line") ;;
    removed) REMOVED+=("$line") ;;
    *) CHANGED+=("$line") ;;
  esac
done

VERSION="$(date -u +%Y.%m.%d)"
{
  echo "# Changelog"
  echo
  echo "All notable changes to this project are documented here."
  echo
  echo "## [${VERSION}] - $(date -u +%Y-%m-%d)"
  echo
  echo "${SINCE_LINE}"
  echo

  if ((${#ADDED[@]})); then
    echo "### Added"
    printf '%s\n' "${ADDED[@]}"
    echo
  fi
  if ((${#FIXED[@]})); then
    echo "### Fixed"
    printf '%s\n' "${FIXED[@]}"
    echo
  fi
  if ((${#CHANGED[@]})); then
    echo "### Changed"
    printf '%s\n' "${CHANGED[@]}"
    echo
  fi
  if ((${#REMOVED[@]})); then
    echo "### Removed"
    printf '%s\n' "${REMOVED[@]}"
    echo
  fi

  if ((${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} == 0)); then
    echo "_No commits found in range._"
    echo
  fi
} >"$OUTPUT"

echo "Wrote ${OUTPUT} ($((${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]})) entries)"