#!/usr/bin/env bash
# changelog.sh — structured CHANGELOG.md from git history since last tag
set -euo pipefail

REPO_ROOT="${1:-.}"
OUT_ARG="${2:-CHANGELOG.md}"

# Resolve absolute paths before cd
REPO_ROOT="$(cd "$REPO_ROOT" && pwd)"
if [[ "$OUT_ARG" = /* ]]; then
  OUT_FILE="$OUT_ARG"
else
  # default: write next to caller cwd if relative path given from original cwd
  OUT_FILE="$(pwd)/$OUT_ARG"
fi

cd "$REPO_ROOT"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "error: not a git repository: $REPO_ROOT" >&2
  exit 1
fi

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "${LAST_TAG}" ]]; then
  HEADER_RANGE="since ${LAST_TAG}"
  COMMIT_ARGS=("${LAST_TAG}..HEAD")
else
  HEADER_RANGE="full history (no tags found)"
  COMMIT_ARGS=()
fi

TODAY="$(date -u +%Y-%m-%d)"
REPO_NAME="$(basename "$(git rev-parse --show-toplevel)")"
HEAD_SHA="$(git rev-parse --short HEAD)"

# Collect commit subjects (no merges)
if ((${#COMMIT_ARGS[@]})); then
  mapfile -t COMMITS < <(git log --no-merges --pretty=format:'%s' "${COMMIT_ARGS[@]}")
else
  mapfile -t COMMITS < <(git log --no-merges --pretty=format:'%s')
fi

ADDED=()
FIXED=()
CHANGED=()
REMOVED=()

categorize() {
  local s="$1"
  local lower
  lower="$(printf '%s' "$s" | tr '[:upper:]' '[:lower:]')"
  if [[ "$lower" =~ ^(feat|feature)(\(.+\))?(!)?: ]] || [[ "$lower" =~ ^(add|added|introduce|create|implement|new)[[:space:]] ]]; then
    ADDED+=("$s"); return
  fi
  if [[ "$lower" =~ ^fix(\(.+\))?(!)?: ]] || [[ "$lower" =~ ^(fix|fixed|bug|bugfix|hotfix|patch|resolve|repair)[[:space:]] ]]; then
    FIXED+=("$s"); return
  fi
  if [[ "$lower" =~ ^remove(\(.+\))?(!)?: ]] || [[ "$lower" =~ ^(remove|removed|delete|deleted|drop|dropped|deprecate|deprecated)[[:space:]] ]]; then
    REMOVED+=("$s"); return
  fi
  if [[ "$lower" =~ ^(docs|style|refactor|perf|test|build|ci|chore|revert|change|changed|update|updated|improve|improved|enhance|rename|move|bump)(\(.+\))?(!)?: ]] \
     || [[ "$lower" =~ ^(change|changed|update|updated|refactor|chore|improve|improved|enhance|perf|docs|style|rename|move|bump)[[:space:]] ]]; then
    CHANGED+=("$s"); return
  fi
  # default bucket
  CHANGED+=("$s")
}

for c in "${COMMITS[@]+"${COMMITS[@]}"}"; do
  [[ -z "${c// }" ]] && continue
  categorize "$c"
done

section() {
  local title="$1"
  shift
  # remaining args are items
  echo "### ${title}"
  if (($#==0)); then
    echo "- _(none)_"
  else
    local item
    for item in "$@"; do
      [[ -z "${item// }" ]] && continue
      echo "- ${item}"
    done
  fi
  echo
}

mkdir -p "$(dirname "$OUT_FILE")"
{
  echo "# Changelog"
  echo
  echo "Repository: **${REPO_NAME}**"
  echo
  echo "## [${HEAD_SHA}] - ${TODAY}"
  echo
  echo "_Generated ${HEADER_RANGE}_"
  echo
  section "Added" ${ADDED[@]+"${ADDED[@]}"}
  section "Fixed" ${FIXED[@]+"${FIXED[@]}"}
  section "Changed" ${CHANGED[@]+"${CHANGED[@]}"}
  section "Removed" ${REMOVED[@]+"${REMOVED[@]}"}
} > "$OUT_FILE"

COUNT=${#COMMITS[@]}
echo "Wrote ${OUT_FILE} (${COUNT} commits categorized)"
