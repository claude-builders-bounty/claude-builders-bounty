#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history.
# Bounty #1: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1
#
# Usage:
#   bash changelog.sh                 # commits since last tag -> CHANGELOG.md
#   bash changelog.sh --stdout        # print instead of writing
#   bash changelog.sh --from v1.2.0   # commits since a specific ref
#   bash changelog.sh --version 1.3.0 # label the new section
#   bash changelog.sh --out docs/CHANGELOG.md
#
# Categorizes commits into Added / Fixed / Changed / Removed using
# Conventional Commits prefixes, with a keyword fallback for plain messages.
# Re-running PREPENDS a new section, preserving prior releases.

set -euo pipefail

OUT="CHANGELOG.md"
TO_STDOUT=0
FROM_REF=""
VERSION=""

usage() {
  sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --stdout)  TO_STDOUT=1; shift ;;
    --from)    FROM_REF="${2:-}"; shift 2 ;;
    --version) VERSION="${2:-}"; shift 2 ;;
    --out)     OUT="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage >&2; exit 2 ;;
  esac
done

# --- Resolve the base ref -----------------------------------------------------
if [[ -z "$FROM_REF" ]]; then
  FROM_REF="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi
if [[ -z "$FROM_REF" ]]; then
  RANGE="HEAD"                       # no tags: use full history
  RANGE_LABEL="initial"
else
  RANGE="${FROM_REF}..HEAD"
  RANGE_LABEL="$FROM_REF"
fi

# --- Collect commits (hash<TAB>subject) --------------------------------------
COMMITS="$(git log --no-merges --pretty=format:'%h%x09%s' "$RANGE" 2>/dev/null || true)"
if [[ -z "$COMMITS" ]]; then
  echo "No commits found in range '$RANGE_LABEL'. Nothing to do." >&2
  exit 0
fi

# --- Categorize ---------------------------------------------------------------
declare -a ADDED=() FIXED=() CHANGED=() REMOVED=() OTHER=()

classify() {
  local subject="$1"
  local lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"

  # Conventional Commits prefix wins.
  case "$lower" in
    feat:*|feat\(*\):*|feature:*|add:*|adds:*|added:*) echo ADDED; return ;;
    fix:*|fix\(*\):*|bugfix:*|hotfix:*|bug:*)          echo FIXED; return ;;
    refactor:*|refactor\(*\):*|perf:*|perf\(*\):*|chore:*|chore\(*\):*|docs:*|docs\(*\):*|style:*|style\(*\):*|change:*|update:*|improve:*|enhance:*) echo CHANGED; return ;;
    remove:*|removes:*|removed:*|delete:*|deletes:*|deleted:*|revert:*|revert\(*\):*) echo REMOVED; return ;;
  esac

  # Keyword fallback for plain messages.
  case "$lower" in
    *"fix"*|*"bug"*|*"patch"*|*"repair"*|*"resolve"*|*"correct"*) echo FIXED; return ;;
    *"add"*|*"introduce"*|*"implement"*|*"support"*|*"new "*)      echo ADDED; return ;;
    *"remove"*|*"delete"*|*"drop"*|*"revert"*|*"deprecat"*)         echo REMOVED; return ;;
    *"update"*|*"change"*|*"refactor"*|*"improve"*|*"rename"*|*"bump"*|*"upgrade"*|*"move"*) echo CHANGED; return ;;
  esac
  echo OTHER
}

# Strip a leading Conventional-Commits prefix ("feat(api): " -> "pagination ...").
strip_prefix() {
  local s="$1"
  if [[ "$s" =~ ^[A-Za-z]+(\([^\)]*\))?!?:\ *(.*)$ ]]; then
    printf '%s' "${BASH_REMATCH[2]}"
  else
    printf '%s' "$s"
  fi
}

while IFS=$'\t' read -r hash subject; do
  [[ -z "$hash" ]] && continue
  clean="$(strip_prefix "$subject")"
  case "$(classify "$subject")" in
    ADDED)   ADDED+=("$clean (\`$hash\`)") ;;
    FIXED)   FIXED+=("$clean (\`$hash\`)") ;;
    CHANGED) CHANGED+=("$clean (\`$hash\`)") ;;
    REMOVED) REMOVED+=("$clean (\`$hash\`)") ;;
    *)       OTHER+=("$clean (\`$hash\`)") ;;
  esac
done <<< "$COMMITS"

# --- Render -------------------------------------------------------------------
DATE="$(date -u +%Y-%m-%d)"
HEADER="## ${VERSION:-Unreleased} - ${DATE}"

render_section() {
  local title="$1"; shift
  local -a items=("$@")
  [[ ${#items[@]} -eq 0 ]] && return 0
  printf '### %s\n' "$title"
  for it in "${items[@]}"; do
    printf -- '- %s\n' "$it"
  done
  printf '\n'
}

BODY="$( {
  render_section "Added"   ${ADDED[@]+"${ADDED[@]}"}
  render_section "Fixed"   ${FIXED[@]+"${FIXED[@]}"}
  render_section "Changed" ${CHANGED[@]+"${CHANGED[@]}"}
  render_section "Removed" ${REMOVED[@]+"${REMOVED[@]}"}
  render_section "Other"   ${OTHER[@]+"${OTHER[@]}"}
} )"

SECTION="$HEADER

_Changes since \`${RANGE_LABEL}\` (range \`${RANGE}\`)._

${BODY}"

# --- Write (prepend, preserving prior releases) -------------------------------
if [[ "$TO_STDOUT" -eq 1 ]]; then
  printf '%s\n' "$SECTION"
  exit 0
fi

mkdir -p "$(dirname "$OUT")"
if [[ -f "$OUT" ]]; then
  # Keep the existing "# Changelog" title + preamble, insert the new section
  # directly above the oldest existing release section.
  TITLE_LINE="$(head -n 1 "$OUT")"
  if [[ "$TITLE_LINE" == "# Changelog" ]]; then
    PREAMBLE="$(awk 'NR>1 && /^## /{exit} NR>1{print}' "$OUT")"
    REST="$(awk '/^## /{found=1} found{print}' "$OUT")"
    {
      printf '# Changelog\n'
      [[ -n "$PREAMBLE" ]] && printf '%s\n' "$PREAMBLE"
      printf '%s\n' "$SECTION"
      [[ -n "$REST" ]] && printf '%s\n' "$REST"
    } > "${OUT}.tmp"
  else
    { printf '%s\n' "$SECTION"; cat "$OUT"; } > "${OUT}.tmp"
  fi
  mv "${OUT}.tmp" "$OUT"
else
  {
    printf '# Changelog\n\n'
    printf 'All notable changes to this project are documented here.\n\n'
    printf '%s\n' "$SECTION"
  } > "$OUT"
fi

echo "Wrote ${OUT} (range: ${RANGE_LABEL}, ${#ADDED[@]} added / ${#FIXED[@]} fixed / ${#CHANGED[@]} changed / ${#REMOVED[@]} removed)" >&2
