#!/usr/bin/env bash
set -euo pipefail

# changelog.sh — Auto-generate CHANGELOG.md from git history
# Usage: bash changelog.sh
# Works in any git repo. Fetches all commits since the last tag,
# categorizes them, and writes a formatted CHANGELOG.md.

OUTPUT_FILE="CHANGELOG.md"

# ── 1. Validate we are in a git repo ──────────────────────────────
if ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo "Error: not inside a git repository." >&2
    exit 1
fi

# ── 2. Determine the last tag ─────────────────────────────────────
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -z "$LAST_TAG" ]; then
    echo "No tags found. Including all commits since the beginning."
    TAG_RANGE="HEAD"
    VERSION="0.1.0"
else
    VERSION="$LAST_TAG"
    TAG_RANGE="$LAST_TAG..HEAD"
fi

# ── 3. Gather commits ─────────────────────────────────────────────
COMMITS=$(git log "$TAG_RANGE" --oneline --no-decorate 2>/dev/null || echo "")
if [ -z "$COMMITS" ]; then
    echo "No new commits since the last tag ($LAST_TAG). Nothing to do."
    exit 0
fi

COUNT=$(echo "$COMMITS" | grep -c '' || true)
echo "Found $COUNT new commit(s) since ${LAST_TAG:-the beginning}."

# ── 4. Categorise commits ─────────────────────────────────────────
# We match the conventional-commit type prefix.
# Patterns:
#   feat / feature       →  Added
#   fix                  →  Fixed
#   refactor / style
#     / perf / chore     →  Changed
#   remove / deprecate
#     / deprecated
#     / revert           →  Removed
#   Everything else      →  Changed (default)

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r line; do
    [ -z "$line" ] && continue
    msg="${line#* }"

    # Extract the conventional-commit type (e.g. "feat", "fix(scoped)", "refactor!")
    type_raw=""
    # Match type at start: word followed by optional (scope), optional !, then :
    if [[ "$msg" =~ ^[a-zA-Z]+ ]]; then
        type_raw="${BASH_REMATCH[0]}"
    fi

    type_lower=$(echo "$type_raw" | tr '[:upper:]' '[:lower:]')

    case "$type_lower" in
        feat|feature)
            ADDED+="* ${msg}"$'\n'
            ;;
        fix)
            FIXED+="* ${msg}"$'\n'
            ;;
        refactor|style|perf|chore)
            CHANGED+="* ${msg}"$'\n'
            ;;
        remove|deprecate|deprecated|revert)
            REMOVED+="* ${msg}"$'\n'
            ;;
        *)
            # Default: Changed (catches "test:", "docs:", and plain messages)
            CHANGED+="* ${msg}"$'\n'
            ;;
    esac
done <<< "$COMMITS"

# ── 5. Write the changelog file ───────────────────────────────────
DATE=$(date +%Y-%m-%d)

# Remove trailing blank lines
ADDED=$(echo "$ADDED" | sed '/^$/d')
FIXED=$(echo "$FIXED" | sed '/^$/d')
CHANGED=$(echo "$CHANGED" | sed '/^$/d')
REMOVED=$(echo "$REMOVED" | sed '/^$/d')

{
    echo "## [${VERSION}] - ${DATE}"
    echo ""

    if [ -n "$ADDED" ]; then
        echo "### Added"
        echo ""
        echo "$ADDED"
        echo ""
    fi

    if [ -n "$FIXED" ]; then
        echo "### Fixed"
        echo ""
        echo "$FIXED"
        echo ""
    fi

    if [ -n "$CHANGED" ]; then
        echo "### Changed"
        echo ""
        echo "$CHANGED"
        echo ""
    fi

    if [ -n "$REMOVED" ]; then
        echo "### Removed"
        echo ""
        echo "$REMOVED"
        echo ""
    fi
} > "$OUTPUT_FILE"

echo "✅ Wrote $OUTPUT_FILE (${VERSION})"
echo ""
echo "--- preview ---"
cat "$OUTPUT_FILE"
