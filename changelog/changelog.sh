#!/usr/bin/env bash
#
# changelog.sh — Generate structured CHANGELOG.md from git history
#
# Usage:
#   ./changelog.sh                    # Generate CHANGELOG.md for commits since last tag
#   ./changelog.sh -o CHANGELOG.md    # Write to a custom output file
#   ./changelog.sh -v v1.0.0          # Start from a specific tag (default: latest tag)
#   ./changelog.sh -s v1.0.0..HEAD    # Use an arbitrary git revision range
#
# Categorization (conventional commits):
#   feat:*      → Added
#   fix:*       → Fixed
#   revert:*    → Removed
#   chore:*, refactor:*, docs:*, style:*, perf:*, test:*, ci:*, build:* → Changed
#   everything else → Changed

set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
OUTPUT="CHANGELOG.md"
FROM_TAG=""
REV_RANGE=""
VERSION="Unreleased"
REPO_DIR="."

# ── Help ──────────────────────────────────────────────────────────────────────
usage() {
    cat <<'EOF'
Usage: changelog.sh [OPTIONS]

Generate structured CHANGELOG.md from git history using conventional-commit
categorization (feat → Added, fix → Fixed, revert → Removed, rest → Changed).

Options:
  -o FILE       Write output to FILE (default: CHANGELOG.md)
  -v TAG        Start changelog from TAG (default: latest git tag; if none, first commit)
  -s RANGE      Use an arbitrary git revision range (e.g., "v1.0.0..HEAD")
  -V VERSION    Version string for the changelog header (default: "Unreleased")
  -d DIR        Path to the git repository (default: current directory)
  -h            Show this help message

Examples:
  ./changelog.sh                        # Generate since last tag
  ./changelog.sh -v v1.0.0 -V v1.1.0   # From v1.0.0, label as v1.1.0
  ./changelog.sh -s "v1.0.0..v1.1.0"   # Explicit range
EOF
    exit 0
}

# ── Parse arguments ───────────────────────────────────────────────────────────
while getopts "o:v:s:V:d:h" opt; do
    case "$opt" in
        o) OUTPUT="$OPTARG" ;;
        v) FROM_TAG="$OPTARG" ;;
        s) REV_RANGE="$OPTARG" ;;
        V) VERSION="$OPTARG" ;;
        d) REPO_DIR="$OPTARG" ;;
        h) usage ;;
        *) usage ;;
    esac
done

# ── Enter repo ────────────────────────────────────────────────────────────────
if [[ ! -d "$REPO_DIR/.git" ]]; then
    echo "ERROR: $REPO_DIR is not a git repository." >&2
    exit 1
fi
cd "$REPO_DIR"

# ── Determine commit range ────────────────────────────────────────────────────
if [[ -n "$REV_RANGE" ]]; then
    # User-supplied range — use as-is
    RANGE="$REV_RANGE"
elif [[ -n "$FROM_TAG" ]]; then
    RANGE="$FROM_TAG..HEAD"
else
    # Auto-detect: use latest tag, or first commit if no tags exist
    LATEST_TAG=$(git tag --sort=-creatordate --merged HEAD 2>/dev/null | head -1 || true)
    if [[ -n "$LATEST_TAG" ]]; then
        RANGE="$LATEST_TAG..HEAD"
    else
        # No tags — grab all commits on current branch
        RANGE="HEAD"
    fi
fi

# ── Gather commits ────────────────────────────────────────────────────────────
COMMITS=$(git log "$RANGE" --no-merges --format="%H" 2>/dev/null || true)

if [[ -z "$COMMITS" ]]; then
    echo "No commits found in range: $RANGE" >&2
    # Still produce a valid (empty) changelog
    cat > "$OUTPUT" <<EOF
# Changelog

## $VERSION ($(date +%Y-%m-%d))

No changes since previous release.
EOF
    echo "✓ Empty changelog written to $OUTPUT"
    exit 0
fi

# ── Categorize commits ────────────────────────────────────────────────────────
# Arrays for each category (using temp files to avoid subshell issues)
ADDED_TMP=$(mktemp)
FIXED_TMP=$(mktemp)
CHANGED_TMP=$(mktemp)
REMOVED_TMP=$(mktemp)
trap 'rm -f "$ADDED_TMP" "$FIXED_TMP" "$CHANGED_TMP" "$REMOVED_TMP"' EXIT

while IFS= read -r hash; do
    # Get the full subject line (first line of commit message)
    SUBJECT=$(git log -1 --format="%s" "$hash")

    # Skip empty subjects
    [[ -z "$SUBJECT" ]] && continue

    # Format the entry: "- {subject} ({short_hash})"
    SHORT_HASH="${hash:0:7}"
    ENTRY="- ${SUBJECT} (${SHORT_HASH})"

    # Categorize by conventional-commit prefix
    # Pattern: type(optional-scope): description
    if echo "$SUBJECT" | grep -qiE '^(feat|feature)[(:]'; then
        echo "$ENTRY" >> "$ADDED_TMP"
    elif echo "$SUBJECT" | grep -qiE '^fix[(:]'; then
        echo "$ENTRY" >> "$FIXED_TMP"
    elif echo "$SUBJECT" | grep -qiE '^(revert|remove|drop)[(:]'; then
        echo "$ENTRY" >> "$REMOVED_TMP"
    else
        # chore, refactor, docs, style, perf, test, ci, build, or anything else
        echo "$ENTRY" >> "$CHANGED_TMP"
    fi
done <<< "$COMMITS"

# ── Generate CHANGELOG.md ─────────────────────────────────────────────────────
TODAY=$(date +%Y-%m-%d)

{
    echo "# Changelog"
    echo ""
    echo "## $VERSION ($TODAY)"
    echo ""

    # ── Added ──
    if [[ -s "$ADDED_TMP" ]]; then
        echo "### Added"
        echo ""
        sort "$ADDED_TMP"
        echo ""
    fi

    # ── Fixed ──
    if [[ -s "$FIXED_TMP" ]]; then
        echo "### Fixed"
        echo ""
        sort "$FIXED_TMP"
        echo ""
    fi

    # ── Changed ──
    if [[ -s "$CHANGED_TMP" ]]; then
        echo "### Changed"
        echo ""
        sort "$CHANGED_TMP"
        echo ""
    fi

    # ── Removed ──
    if [[ -s "$REMOVED_TMP" ]]; then
        echo "### Removed"
        echo ""
        sort "$REMOVED_TMP"
        echo ""
    fi
} > "$OUTPUT"

# ── Summary ───────────────────────────────────────────────────────────────────
ADDED_COUNT=$(wc -l < "$ADDED_TMP" 2>/dev/null || echo 0)
FIXED_COUNT=$(wc -l < "$FIXED_TMP" 2>/dev/null || echo 0)
CHANGED_COUNT=$(wc -l < "$CHANGED_TMP" 2>/dev/null || echo 0)
REMOVED_COUNT=$(wc -l < "$REMOVED_TMP" 2>/dev/null || echo 0)
TOTAL=$((ADDED_COUNT + FIXED_COUNT + CHANGED_COUNT + REMOVED_COUNT))

echo "✓ CHANGELOG.md generated — $TOTAL commits"
echo "  Added:   $ADDED_COUNT"
echo "  Fixed:   $FIXED_COUNT"
echo "  Changed: $CHANGED_COUNT"
echo "  Removed: $REMOVED_COUNT"
