#!/usr/bin/env bash
set -euo pipefail

OUT=${1:-CHANGELOG.md}
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
if [[ -n "$LAST_TAG" ]]; then
  RANGE="$LAST_TAG..HEAD"
  SINCE="since $LAST_TAG"
else
  RANGE="HEAD"
  SINCE="for all history"
fi

COMMITS=$(git log --no-merges --pretty=format:'%s' "$RANGE" 2>/dev/null || true)
TODAY=$(date +%Y-%m-%d)

ADDED_FILE=$(mktemp)
FIXED_FILE=$(mktemp)
CHANGED_FILE=$(mktemp)
REMOVED_FILE=$(mktemp)
trap 'rm -f "$ADDED_FILE" "$FIXED_FILE" "$CHANGED_FILE" "$REMOVED_FILE"' EXIT
while IFS= read -r msg; do
  [[ -z "$msg" ]] && continue
  low=$(printf '%s' "$msg" | tr '[:upper:]' '[:lower:]')
  case "$low" in
    fix:*|fixed:*|bugfix:*|*fix*|*bug*) printf '%s\n' "$msg" >> "$FIXED_FILE" ;;
    remove:*|removed:*|delete:*|deleted:*|*remove*|*delete*) printf '%s\n' "$msg" >> "$REMOVED_FILE" ;;
    add:*|added:*|feat:*|feature:*|*add*|*implement*) printf '%s\n' "$msg" >> "$ADDED_FILE" ;;
    change:*|changed:*|refactor:*|update:*|updated:*|*change*|*update*|*refactor*) printf '%s\n' "$msg" >> "$CHANGED_FILE" ;;
    *) printf '%s\n' "$msg" >> "$CHANGED_FILE" ;;
  esac
done <<< "$COMMITS"

section() {
  local title=$1
  local file=$2
  printf '### %s\n' "$title"
  if [[ ! -s "$file" ]]; then
    printf -- '- Nothing recorded.\n\n'
  else
    sed 's/^/- /' "$file"
    printf '\n'
  fi
}

{
  printf '# Changelog\n\n'
  printf '## %s — generated %s\n\n' "$TODAY" "$SINCE"
  section Added "$ADDED_FILE"
  section Fixed "$FIXED_FILE"
  section Changed "$CHANGED_FILE"
  section Removed "$REMOVED_FILE"
} > "$OUT"

echo "Generated $OUT ($SINCE)"
