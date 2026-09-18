#!/usr/bin/env bash
# changelog.sh — generate a structured CHANGELOG.md from git history.
# Dependency-free: bash + git only.
#
# Usage:
#   bash changelog.sh                       # writes CHANGELOG.md since the last tag
#   CHANGELOG_OUT=- bash changelog.sh       # print to stdout only
#   CHANGELOG_SINCE=v1.0.0 bash changelog.sh
set -euo pipefail

OUT="${CHANGELOG_OUT:-CHANGELOG.md}"
TITLE="${CHANGELOG_TITLE:-# Changelog}"
CATS="${CHANGELOG_CATEGORIES:-Added,Fixed,Changed,Removed}"

# --- resolve range -----------------------------------------------------------
SINCE="${CHANGELOG_SINCE:-}"
if [[ -z "$SINCE" ]]; then
  LAST_TAG="$(git describe --abbrev=0 --tags 2>/dev/null || true)"
  [[ -n "$LAST_TAG" ]] && SINCE="$LAST_TAG"
fi

if [[ -n "$SINCE" ]]; then
  RANGE="${SINCE}..HEAD"
  RANGE_LABEL="${SINCE}..HEAD"
else
  RANGE="HEAD"
  RANGE_LABEL="all history"
fi

# --- collect commits ---------------------------------------------------------
# Fail loudly when the requested range is invalid. A typo'd tag or running
# outside a repo would otherwise silently produce an empty changelog.
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "changelog.sh: not inside a git repository" >&2
  exit 1
fi
if [[ -n "$SINCE" ]]; then
  if ! git rev-parse --verify --quiet "${SINCE}^{commit}" >/dev/null 2>&1; then
    echo "changelog.sh: invalid git range '${SINCE}' (tag/commit not found)" >&2
    exit 1
  fi
fi
RAW="$(git log --pretty=format:'%h|%s' "$RANGE")"

# --- categorize (no associative arrays, portable to stock bash 3.2) ----------
declare -a CAT_ARR=()
IFS=',' read -ra CAT_ARR <<< "$CATS"
for i in "${!CAT_ARR[@]}"; do
  CAT_ARR[$i]="$(printf '%s' "${CAT_ARR[$i]}" | xargs)"
done

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

while IFS='|' read -r hash subject; do
  [[ -z "$hash" ]] && continue
  # Recognize conventional-commit subjects with optional scope/breaking marker:
#   feat(api)!, fix(scope):, revert:, etc.
PAT_ADDED='^(feat|add|new|feature)(\([^)]*\))?(!)?:'
PAT_FIXED='^(fix|bugfix|hotfix|revert)(\([^)]*\))?(!)?:'
PAT_REMOVED='^(remove|delete|rm)(\([^)]*\))?(!)?:'
if [[ "$subject" =~ $PAT_ADDED ]]; then
    key="Added"
elif [[ "$subject" =~ $PAT_FIXED ]]; then
    key="Fixed"
elif [[ "$subject" =~ $PAT_REMOVED ]]; then
    key="Removed"
else
    key="Changed"
fi
  # only honor categories the caller requested; anything else folds into Changed
  found=0
  for c in "${CAT_ARR[@]}"; do [[ "$c" == "$key" ]] && found=1 && break; done
  [[ "$found" -eq 0 ]] && key="Changed"
  printf '%s\t%s\n' "$key" "${hash}  ${subject}" >> "$TMP"
done <<< "$RAW"

emit_section() {
  local label="$1" file="$2" line
  [[ ! -s "$file" ]] && return 0
  printf '## %s\n\n' "$label"
  while IFS= read -r line; do
    printf -- '- %s\n' "$line"
  done < "$file"
}

DOC="$(
  {
    printf '%s\n\n' "$TITLE"
    printf '_Generated %s from git range `%s`._\n\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$RANGE_LABEL"
    for c in "${CAT_ARR[@]}"; do
      f="$(mktemp)"
      while IFS=$'\t' read -r k line; do
        [[ "$k" == "$c" ]] && printf '%s\n' "$line" >> "$f"
      done < "$TMP"
      emit_section "$c" "$f"
      rm -f "$f"
    done
  }
)"

if [[ "$OUT" == "-" ]]; then
  printf '%s\n' "$DOC"
else
  printf '%s\n' "$DOC" > "$OUT"
  cat "$OUT"
fi