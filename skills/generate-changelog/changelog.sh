#!/usr/bin/env bash
# Generate a structured CHANGELOG.md from git history since the last tag.
set -euo pipefail

OUT="${1:-CHANGELOG.md}"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || echo "")"
if [[ -n "$LAST_TAG" ]]; then
  RANGE="${LAST_TAG}..HEAD"
  SINCE_LINE="Changes since \`${LAST_TAG}\`."
else
  RANGE="HEAD"
  SINCE_LINE="Initial changelog (no prior git tag found)."
fi

mapfile -t COMMITS < <(git log "$RANGE" --pretty=format:%s)

added=()
fixed=()
changed=()
removed=()

categorize() {
  local subject="$1"
  local lower
  lower="$(echo "$subject" | tr '[:upper:]' '[:lower:]')"

  if [[ "$lower" =~ ^(fix|bugfix|hotfix|patch) ]]; then
    fixed+=("$subject")
  elif [[ "$lower" =~ ^(remove|delete|drop) ]]; then
    removed+=("$subject")
  elif [[ "$lower" =~ ^(change|refactor|chore|perf|style|build|ci|test) ]]; then
    changed+=("$subject")
  elif [[ "$lower" =~ ^(feat|add|new|introduce|implement) ]]; then
    added+=("$subject")
  else
    changed+=("$subject")
  fi
}

for c in "${COMMITS[@]}"; do
  [[ -z "$c" ]] && continue
  categorize "$c"
done

section() {
  local title="$1"
  shift
  local -n items=("$1")
  if ((${#items[@]} == 0)); then
    return
  fi
  echo "### $title"
  echo
  for item in "${items[@]}"; do
    echo "- $item"
  done
  echo
}

DATE="$(date -u +%Y-%m-%d)"
{
  echo "# Changelog"
  echo
  echo "## [$DATE]"
  echo
  echo "$SINCE_LINE"
  echo
  section "Added" added
  section "Fixed" fixed
  section "Changed" changed
  section "Removed" removed
} > "$OUT"

echo "Wrote $OUT"
