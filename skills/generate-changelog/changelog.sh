#!/usr/bin/env bash
# generate-changelog — build a structured CHANGELOG section from git history.
#
# Usage:
#   bash changelog.sh [--output FILE] [--since TAG] [--version NAME] [--date YYYY-MM-DD]
#
# Behaviour:
#   * Collects commits since the last git tag (or all commits if there is no tag).
#   * Auto-categorizes each commit into Added / Fixed / Changed / Removed
#     using Conventional Commits prefixes, with keyword fallbacks for
#     non-conventional subjects.
#   * Prepends the new section to CHANGELOG.md (creating it with a
#     Keep a Changelog header when missing) and prints it to stdout.
set -euo pipefail

OUTPUT="CHANGELOG.md"
SINCE=""
VERSION="Unreleased"
DATE="$(date +%F)"

while [ $# -gt 0 ]; do
  case "$1" in
    --output)  OUTPUT="$2"; shift 2 ;;
    --since)   SINCE="$2"; shift 2 ;;
    --version) VERSION="$2"; shift 2 ;;
    --date)    DATE="$2"; shift 2 ;;
    -h|--help) grep '^#' "$0" | head -20; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
  echo "error: not inside a git repository" >&2; exit 1;
}

# ---- determine the commit range -------------------------------------------
if [ -z "$SINCE" ]; then
  SINCE="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi

RANGE=""
if [ -n "$SINCE" ]; then
  RANGE="${SINCE}..HEAD"
  # If HEAD *is* the tag, the range is empty: fall back to that release's range.
  if [ -z "$(git rev-list "$RANGE" 2>/dev/null || true)" ]; then
    PREV="$(git describe --tags --abbrev=0 "${SINCE}^" 2>/dev/null || true)"
    if [ -n "$PREV" ]; then RANGE="${PREV}..${SINCE}"; else RANGE="$SINCE"; fi
    [ "$VERSION" = "Unreleased" ] && VERSION="${SINCE#v}"
  fi
fi

# ---- collect and categorize commits ---------------------------------------
ADDED=(); FIXED=(); CHANGED=(); REMOVED=()

capitalize() {
  local s="$1"
  printf '%s%s' "$(printf '%s' "${s:0:1}" | tr '[:lower:]' '[:upper:]')" "${s:1}"
}

add_entry() {
  local bucket="$1" text="$2"
  text="$(capitalize "$text")"
  case "$bucket" in
    added)   ADDED+=("- $text") ;;
    fixed)   FIXED+=("- $text") ;;
    changed) CHANGED+=("- $text") ;;
    removed) REMOVED+=("- $text") ;;
  esac
}

while IFS= read -r subject; do
  [ -z "$subject" ] && continue
  # Skip merge commits and changelog housekeeping to avoid self-reference.
  case "$subject" in
    Merge\ *|*hange\ [Ll]og*|*CHANGELOG*) continue ;;
  esac

  type="" rest="$subject" breaking=0
  if [[ "$subject" =~ ^([A-Za-z]+)(\([^\)]*\))?(!)?:[[:space:]](.+)$ ]]; then
    type="$(printf '%s' "${BASH_REMATCH[1]}" | tr '[:upper:]' '[:lower:]')"
    [ -n "${BASH_REMATCH[3]}" ] && breaking=1
    rest="${BASH_REMATCH[4]}"
  fi
  lower_rest="$(printf '%s' "$rest" | tr '[:upper:]' '[:lower:]')"

  bucket=""
  # Removals: an explicit remove/deprecate type always counts. A leading
  # remove/delete/drop keyword also counts for untyped commits and for
  # "chore:" (which carries no semantics of its own). A typed commit like
  # "refactor!: drop support for X" stays in its type's bucket.
  if [ "$type" = "remove" ] || [ "$type" = "deprecate" ] || \
     { { [ -z "$type" ] || [ "$type" = "chore" ]; } && \
       [[ "$lower_rest" =~ ^(remove|removed|delete|deleted|drop|dropped)[[:space:]] ]]; }; then
    bucket="removed"
  else
    case "$type" in
      feat|feature) bucket="added" ;;
      fix|bugfix|hotfix) bucket="fixed" ;;
      perf|refactor|style|docs|chore|build|ci|test|revert) bucket="changed" ;;
      *)
        case "$lower_rest" in
          add\ *|added\ *|introduce\ *|new\ *) bucket="added" ;;
          fix\ *|fixed\ *|resolve\ *|resolved\ *) bucket="fixed" ;;
          *) bucket="changed" ;;
        esac
        ;;
    esac
  fi

  [ "$breaking" = "1" ] && rest="**Breaking:** $rest"
  add_entry "$bucket" "$rest"
done < <(git log --no-merges --pretty=tformat:'%s' $RANGE 2>/dev/null || git log --no-merges --pretty=tformat:'%s')

TOTAL=$(( ${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} ))
if [ "$TOTAL" -eq 0 ]; then
  echo "no commits found in range '${RANGE:-<all>}' — nothing to write" >&2
  exit 0
fi

# ---- render the section ----------------------------------------------------
SECTION_FILE="$(mktemp)"
{
  echo "## [$VERSION] - $DATE"
  echo
  if [ ${#ADDED[@]} -gt 0 ];   then echo "### Added";   printf '%s\n' "${ADDED[@]}";   echo; fi
  if [ ${#FIXED[@]} -gt 0 ];   then echo "### Fixed";   printf '%s\n' "${FIXED[@]}";   echo; fi
  if [ ${#CHANGED[@]} -gt 0 ]; then echo "### Changed"; printf '%s\n' "${CHANGED[@]}"; echo; fi
  if [ ${#REMOVED[@]} -gt 0 ]; then echo "### Removed"; printf '%s\n' "${REMOVED[@]}"; echo; fi
} > "$SECTION_FILE"

# ---- write into the changelog file ----------------------------------------
if [ -f "$OUTPUT" ]; then
  TMP="$(mktemp)"
  # Insert the new section just before the first existing "## " heading,
  # keeping the file header/intro intact; append if there is none.
  awk -v sec="$SECTION_FILE" '
    /^## / && !done { while ((getline line < sec) > 0) print line; done=1 }
    { print }
    END { if (!done) { while ((getline line < sec) > 0) print line } }
  ' "$OUTPUT" > "$TMP"
  mv "$TMP" "$OUTPUT"
else
  {
    echo "# Changelog"
    echo
    echo "All notable changes to this project will be documented in this file."
    echo
    echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),"
    echo "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)."
    echo
    cat "$SECTION_FILE"
  } > "$OUTPUT"
fi

echo "wrote $TOTAL entries to $OUTPUT (range: ${RANGE:-all history})" >&2
cat "$SECTION_FILE"
rm -f "$SECTION_FILE"
