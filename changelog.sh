#!/usr/bin/env bash
# changelog.sh — generate a structured CHANGELOG.md from git history.
#
# Usage:
#   bash changelog.sh [output_file] [since_ref]
#
#   output_file  default: CHANGELOG.md
#   since_ref    default: latest git tag (or first commit if no tags)
#
# Fetches commits since the last tag, auto-categorizes them into
# Added / Fixed / Changed / Removed, and writes a Keep-a-Changelog style file.

set -euo pipefail

OUT="${1:-CHANGELOG.md}"
SINCE="${2:-}"

# Resolve the "since" reference.
if [[ -z "$SINCE" ]]; then
  SINCE=$(git describe --tags --abbrev=0 2>/dev/null || true)
  if [[ -z "$SINCE" ]]; then
    # No tags: use the first commit.
    SINCE=$(git rev-list --max-parents=0 HEAD 2>/dev/null | head -n1 || true)
  fi
fi

if [[ -z "$SINCE" ]]; then
  echo "error: could not determine a starting reference" >&2
  exit 1
fi

# Version label for the header.
if git describe --tags --abbrev=0 >/dev/null 2>&1; then
  LAST_TAG=$(git describe --tags --abbrev=0)
  NEW_TAG="${LAST_TAG}-unreleased"
else
  NEW_TAG="Unreleased"
fi

DATE=$(date -u +%Y-%m-%d)

# Temp files for categories.
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT
ADDED="$TMPDIR/added.txt"; FIXED="$TMPDIR/fixed.txt"
CHANGED="$TMPDIR/changed.txt"; REMOVED="$TMPDIR/removed.txt"
OTHER="$TMPDIR/other.txt"
: > "$ADDED"; : > "$FIXED"; : > "$CHANGED"; : > "$REMOVED"; : > "$OTHER"

# Collect commits into a temp file first (portable; avoids subshell/proc-sub issues).
COMMITS="$TMPDIR/commits.txt"
# %n ensures a trailing newline so `while read` actually iterates (git's
# pretty=format does not terminate the last line).
git log "${SINCE}..HEAD" --pretty=format:'%h%x09%s%n' --reverse 2>/dev/null > "$COMMITS" || true

while IFS="$(printf '\t')" read -r hash subject; do
  [[ -z "$hash" ]] && continue
  [[ -z "$subject" ]] && continue
  msg="$subject"
  lower=$(printf '%s' "$msg" | tr '[:upper:]' '[:lower:]')
  case "$lower" in
    feat:*|add:*|added:*)        printf -- '- %s (%s)\n' "$msg" "$hash" >> "$ADDED" ;;
    fix:*|fixed:*|bugfix:*)      printf -- '- %s (%s)\n' "$msg" "$hash" >> "$FIXED" ;;
    remove:*|removed:*|deprecat*) printf -- '- %s (%s)\n' "$msg" "$hash" >> "$REMOVED" ;;
    chore:*|refactor:*|perf:*|docs:*|style:*|test:*|ci:*|build:*) \
                                 printf -- '- %s (%s)\n' "$msg" "$hash" >> "$CHANGED" ;;
    *)                           printf -- '- %s (%s)\n' "$msg" "$hash" >> "$OTHER" ;;
  esac
done < "$COMMITS"

# Build the output.
{
  echo "# Changelog"
  echo ""
  echo "## [${NEW_TAG}] - ${DATE}"
  echo ""
  if [[ -s "$ADDED" ]]; then
    echo "### Added"
    echo ""
    cat "$ADDED"
    echo ""
  fi
  if [[ -s "$FIXED" ]]; then
    echo "### Fixed"
    echo ""
    cat "$FIXED"
    echo ""
  fi
  if [[ -s "$CHANGED" ]]; then
    echo "### Changed"
    echo ""
    cat "$CHANGED"
    echo ""
  fi
  if [[ -s "$REMOVED" ]]; then
    echo "### Removed"
    echo ""
    cat "$REMOVED"
    echo ""
  fi
  if [[ -s "$OTHER" ]]; then
    echo "### Other"
    echo ""
    cat "$OTHER"
    echo ""
  fi
  if [[ ! -s "$ADDED" && ! -s "$FIXED" && ! -s "$CHANGED" && ! -s "$REMOVED" && ! -s "$OTHER" ]]; then
    echo "_No commits since ${SINCE}._"
    echo ""
  fi
  echo "---"
  echo "_Generated from commits since \`${SINCE}\`._"
} > "$OUT"

echo "Wrote $OUT (commits since $SINCE)"
