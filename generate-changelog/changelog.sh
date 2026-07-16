#!/usr/bin/env bash
#
# changelog.sh — Generate a structured CHANGELOG.md from git history.
# NullPointerCo (MIT). Works as a standalone script or via `/generate-changelog`.
#
# Usage:
#   bash changelog.sh [OUTPUT_PATH]
#
#   OUTPUT_PATH  Where to write the changelog (default: ./CHANGELOG.md)
#
# Behavior:
#   - Fetches commits since the last git tag (or all commits if untagged)
#   - Auto-categorizes into Added / Fixed / Changed / Removed
#   - Appends a new versioned entry (dated) to the top of the existing CHANGELOG
#
set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"

# --- Determine the range: from last tag to HEAD -----------------------------
LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "$LAST_TAG" ]; then
  RANGE="${LAST_TAG}..HEAD"
  VERSION_BASE="$LAST_TAG"
else
  RANGE=""
  VERSION_BASE="v0.0.0"
fi

# Bump the patch segment for the new entry heading
if [[ "$VERSION_BASE" =~ ^v?([0-9]+)\.([0-9]+)\.([0-9]+)$ ]]; then
  MAJ=${BASH_REMATCH[1]}; MIN=${BASH_REMATCH[2]}; PAT=${BASH_REMATCH[3]}
  NEW_VERSION="v${MAJ}.${MIN}.$((PAT + 1))"
else
  NEW_VERSION="v0.1.0"
fi

TODAY="$(date +%Y-%m-%d)"

# --- Collect commits in the range -------------------------------------------
if [ -n "$RANGE" ]; then
  COMMITS="$(git log "${RANGE}" --pretty=format:'%s')"
else
  COMMITS="$(git log --pretty=format:'%s')"
fi

if [ -z "$COMMITS" ]; then
  echo "No new commits since ${LAST_TAG:-start}. Nothing to add." >&2
  exit 0
fi

# --- Categorize -------------------------------------------------------------
ADDED=""; FIXED=""; CHANGED=""; REMOVED=""

while IFS= read -r line; do
  [ -z "$line" ] && continue
  clean="$(echo "$line" | sed -E 's/^\([a-z]+\)\s*//; s/^\[[a-z]+\]\s*//')"
  low="$(echo "$line" | tr '[:upper:]' '[:lower:]')"
  entry="- ${clean}"
  if   [[ "$low" =~ ^feat|add|^(add|new|create|implement) ]]; then ADDED+="${entry}\n"
  elif [[ "$low" =~ ^fix|bug|resolve|patch ]]; then            FIXED+="${entry}\n"
  elif [[ "$low" =~ ^refactor|update|change|improve|chore|perf|docs ]]; then CHANGED+="${entry}\n"
  elif [[ "$low" =~ ^remove|delete|drop ]]; then               REMOVED+="${entry}\n"
  else                                                          CHANGED+="${entry}\n"
  fi
done <<< "$COMMITS"

# --- Build the new entry block ----------------------------------------------
block="## ${NEW_VERSION} — ${TODAY}\n\n"

if [ -n "$ADDED" ];   then block+="### Added\n${ADDED}\n"; fi
if [ -n "$CHANGED" ]; then block+="### Changed\n${CHANGED}\n"; fi
if [ -n "$FIXED" ];   then block+="### Fixed\n${FIXED}\n"; fi
if [ -n "$REMOVED" ]; then block+="### Removed\n${REMOVED}\n"; fi

block+="\n"

# --- Merge with any existing CHANGELOG ---------------------------------------
if [ -f "$OUTPUT" ]; then
  # Strip an existing header if present
  EXISTING="$(cat "$OUTPUT")"
  if [[ "$EXISTING" == \#\ [Cc]hangelog* ]]; then
    EXISTING="$(echo "$EXISTING" | sed '1{/^# .*Changelog.*/d}')"
  fi
  {
    printf '# Changelog\n\n'
    printf '%b' "$block"
    printf '%s' "$EXISTING"
  } > "${OUTPUT}.tmp"
  mv "${OUTPUT}.tmp" "$OUTPUT"
else
  {
    printf '# Changelog\n\n'
    printf '%b' "$block"
  } > "$OUTPUT"
fi

echo "Wrote ${NEW_VERSION} entry to ${OUTPUT}"
