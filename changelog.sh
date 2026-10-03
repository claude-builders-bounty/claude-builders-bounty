#!/usr/bin/env bash
#
# changelog.sh — Generate a structured CHANGELOG.md from git history.
#
# Usage:
#   bash changelog.sh              # commits since last tag -> new "Unreleased" section
#   bash changelog.sh v1.2.0       # commits since v1.2.0
#
# Categorizes commits into Added / Fixed / Changed / Removed using
# Conventional Commits prefixes (feat:, fix:, perf:, refactor:, ...) with a
# keyword-based fallback for non-conventional messages.
#
set -euo pipefail

REPO_DIR="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "Error: not inside a git repository." >&2
  exit 1
}
cd "$REPO_DIR"

SINCE_TAG="${1:-}"
CHANGELOG="CHANGELOG.md"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

# ---------------------------------------------------------------- helpers ---
commit_subjects() {
  # Print "%h\t%s" lines for commits since the given ref (or all if empty).
  local range
  if [[ -n "$SINCE_TAG" ]]; then
    range="${SINCE_TAG}..HEAD"
  elif git describe --tags --abbrev=0 >/dev/null 2>&1; then
    SINCE_TAG="$(git describe --tags --abbrev=0)"
    range="${SINCE_TAG}..HEAD"
  else
    range="HEAD" # no tags yet — full history
  fi
  git log --no-merges --no-color --pretty=format:'%h	%s' "$range"
}

categorize() {
  # Read "hash<TAB>subject" lines, bucket them, print "category|hash|subject".
  local hash subject lower
  while IFS=$'\t' read -r hash subject; do
    [[ -z "$hash" ]] && continue
    lower="$(echo "$subject" | tr '[:upper:]' '[:lower:]')"
    local cat=""
    case "$lower" in
      feat*|add*|"support"*) cat="Added" ;;
      fix*|bugfix*|patch*|repair*) cat="Fixed" ;;
      perf*|refactor*|rework*|update*|change*|improve*|modif*) cat="Changed" ;;
      rem*|delet*|drop*|strip*|deprecat*) cat="Removed" ;;
    esac
    # Keyword fallback for non-conventional messages.
    if [[ -z "$cat" ]]; then
      if grep -qE '(add|introduc|new feature|support)' <<<"$lower"; then cat="Added"
      elif grep -qE '(fix|bug|issue|crash|error|regression|resolve)' <<<"$lower"; then cat="Fixed"
      elif grep -qE '(refactor|clean|simplif|renam|rework|update|improv|optimi)' <<<"$lower"; then cat="Changed"
      elif grep -qE '(remove|delete|drop|deprecat|strip)' <<<"$lower"; then cat="Removed"
      else cat="Changed"
      fi
    fi
    printf '%s|%s|%s\n' "$cat" "$hash" "$subject"
  done
}

emit_section() {
  # emit_section <heading> — print "### heading" + matching bullets, if any.
  local heading="$1" lines
  lines="$(grep "^${heading}|" "$1_FILE" 2>/dev/null || true)"
  # shellcheck disable=SC2154  # $1_FILE is set by caller via process substitution
  :
}

# ------------------------------------------------------------------ main ----
CATEGORIZED="$(commit_subjects | categorize)"

NEW_VERSION="Unreleased"
if [[ -n "${SINCE_TAG:-}" ]]; then
  NEW_VERSION="since ${SINCE_TAG}"
fi
TODAY="$(date +%Y-%m-%d)"

{
  echo "# Changelog"
  echo
  echo "All notable changes to this project are documented in this file."
  echo "Generated automatically from git history by \`changelog.sh\`."
  echo
  echo "## ${NEW_VERSION} (${TODAY})"
  echo
} > "$TMP"

ANY=0
for cat in Added Fixed Changed Removed; do
  BULLETS="$(grep "^${cat}|" <<<"$CATEGORIZED" | cut -d'|' -f2- | sed 's/^\(.*\)	\(.*\)$/- \2 (\1)/' || true)"
  if [[ -n "${BULLETS//[$'\t' ]/}" ]]; then
    ANY=1
    echo "### ${cat}" >> "$TMP"
    echo >> "$TMP"
    echo "$BULLETS" >> "$TMP"
    echo >> "$TMP"
  fi
done

if [[ "$ANY" -eq 0 ]]; then
  echo "_No commits found since ${SINCE_TAG:-the beginning of history}._" >> "$TMP"
  echo >> "$TMP"
fi

# Prepend to existing changelog (skip its old header lines).
if [[ -f "$CHANGELOG" ]]; then
  tail -n +6 "$CHANGELOG" >> "$TMP"   # drop previous "# Changelog" header block
fi

mv "$TMP" "$CHANGELOG"
echo "✔ Updated ${CHANGELOG} (${NEW_VERSION})."
echo "  $(grep -c '^- ' "$CHANGELOG" || true) commit(s) categorized."
