#!/usr/bin/env bash
# Generate a structured CHANGELOG.md from git history since the last tag.
# Usage: bash changelog.sh [output-file]
set -euo pipefail

OUT="${1:-CHANGELOG.md}"
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "${ROOT}" ]]; then
  echo "error: not inside a git repository" >&2
  exit 1
fi
cd "$ROOT"

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [[ -n "${LAST_TAG}" ]]; then
  RANGE="${LAST_TAG}..HEAD"
  SINCE_LABEL="since ${LAST_TAG}"
else
  RANGE="HEAD"
  SINCE_LABEL="full history (no tags found)"
fi

# Collect subject lines only.
mapfile -t COMMITS < <(git log ${LAST_TAG:+${LAST_TAG}..}HEAD --pretty=format:'%s' 2>/dev/null || true)

ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
OTHER=()

categorize() {
  local s="$1"
  local lower
  lower="$(printf '%s' "$s" | tr '[:upper:]' '[:lower:]')"
  # Conventional commits + keyword heuristics
  if [[ "$lower" =~ ^(feat|feature)(\(.+\))?: ]] || [[ "$lower" =~ (^|[[:space:]])(add|added|adding|implement|introduce) ]]; then
    ADDED+=("$s")
  elif [[ "$lower" =~ ^(fix)(\(.+\))?: ]] || [[ "$lower" =~ (^|[[:space:]])(fix|fixed|fixes|bugfix|hotfix|patch) ]]; then
    FIXED+=("$s")
  elif [[ "$lower" =~ ^(remove|revert|delete)(\(.+\))?: ]] || [[ "$lower" =~ (^|[[:space:]])(remove|removed|delete|deleted|drop|dropped) ]]; then
    REMOVED+=("$s")
  elif [[ "$lower" =~ ^(chore|refactor|perf|docs|style|build|ci)(\(.+\))?: ]] || [[ "$lower" =~ (^|[[:space:]])(change|changed|update|updated|refactor|improve|bump) ]]; then
    CHANGED+=("$s")
  else
    OTHER+=("$s")
  fi
}

for c in "${COMMITS[@]:-}"; do
  [[ -z "${c// }" ]] && continue
  categorize "$c"
done

# Items that did not match keywords still go to Changed so nothing is lost.
if ((${#OTHER[@]})); then
  for o in "${OTHER[@]}"; do
    CHANGED+=("$o")
  done
fi

DATE_UTC="$(date -u +%Y-%m-%d 2>/dev/null || date +%Y-%m-%d)"
{
  echo "# Changelog"
  echo
  echo "Generated ${DATE_UTC} (${SINCE_LABEL})."
  echo
  section() {
    local title="$1"
    shift
    local -a items=("$@")
    echo "## ${title}"
    echo
    if ((${#items[@]} == 0)); then
      echo "_None_"
    else
      for i in "${items[@]}"; do
        echo "- ${i}"
      done
    fi
    echo
  }
  section "Added" "${ADDED[@]:-}"
  section "Fixed" "${FIXED[@]:-}"
  section "Changed" "${CHANGED[@]:-}"
  section "Removed" "${REMOVED[@]:-}"
} >"$OUT"

echo "Wrote ${OUT} (${SINCE_LABEL}, ${#COMMITS[@]} commit subjects)."
