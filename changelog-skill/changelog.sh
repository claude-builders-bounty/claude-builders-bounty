#!/usr/bin/env bash
# changelog.sh — generate a structured CHANGELOG.md from git history.
# Works with or without tags. Categorizes conventional-commit subjects into
# Added / Fixed / Changed / Removed.
#
# Usage:
#   bash changelog.sh                 # writes ./CHANGELOG.md (since last tag)
#   bash changelog.sh -o out.md       # custom output path
#   bash changelog.sh --all           # include full history (ignore tags)
set -eo pipefail

OUT="CHANGELOG.md"
USE_TAGS=1
while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output) OUT="$2"; shift 2 ;;
    --all) USE_TAGS=0; shift ;;
    -h|--help) echo "Usage: bash changelog.sh [-o FILE] [--all]"; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: not a git repository" >&2
  exit 1
fi

# Determine commit range.
if [[ $USE_TAGS -eq 1 ]]; then
  LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
fi
if [[ -n "${LAST_TAG:-}" ]]; then
  RANGE="${LAST_TAG}..HEAD"
  VERSION="Unreleased (since ${LAST_TAG})"
else
  RANGE=""
  VERSION="Unreleased"
fi

# Collect subject lines.
mapfile -t SUBJECTS < <(git log ${RANGE} --pretty=format:"%s" 2>/dev/null)
if [[ ${#SUBJECTS[@]} -eq 0 ]]; then
  echo "No commits found." >&2
  exit 0
fi

classify() {
  local s="$1"
  local low="${s,,}"
  if [[ "$s" =~ ^feat(\(.*\))?!?: ]]; then echo "Added"
  elif [[ "$s" =~ ^fix(\(.*\))?!?: ]]; then echo "Fixed"
  elif [[ "$s" =~ ^(refactor|perf|style|docs|test|chore|build|ci)(\(.*\))?!?: ]]; then echo "Changed"
  elif [[ "$low" =~ (remove|removes|removed|delete|deletes|deleted) ]]; then echo "Removed"
  elif [[ "$s" =~ ^(add|adds|added) ]]; then echo "Added"
  else echo "Changed"; fi
}

declare -A ADDED FIXED CHANGED REMOVED
for s in "${SUBJECTS[@]}"; do
  [[ -z "$s" ]] && continue
  c=$(classify "$s")
  case "$c" in
    Added) ADDED["$s"]=1 ;;
    Fixed) FIXED["$s"]=1 ;;
    Removed) REMOVED["$s"]=1 ;;
    *) CHANGED["$s"]=1 ;;
  esac
done

DATE=$(date +%Y-%m-%d)
{
  echo "# Changelog"
  echo ""
  echo "## ${VERSION} — ${DATE}"
  echo ""
  if [[ ${#ADDED[@]} -gt 0 ]]; then
    echo "### Added"
    for k in "${!ADDED[@]}"; do echo "- ${k}"; done
    echo ""
  fi
  if [[ ${#FIXED[@]} -gt 0 ]]; then
    echo "### Fixed"
    for k in "${!FIXED[@]}"; do echo "- ${k}"; done
    echo ""
  fi
  if [[ ${#CHANGED[@]} -gt 0 ]]; then
    echo "### Changed"
    for k in "${!CHANGED[@]}"; do echo "- ${k}"; done
    echo ""
  fi
  if [[ ${#REMOVED[@]} -gt 0 ]]; then
    echo "### Removed"
    for k in "${!REMOVED[@]}"; do echo "- ${k}"; done
    echo ""
  fi
} > "$OUT"

echo "Wrote ${OUT} with ${#SUBJECTS[@]} commit(s)."
