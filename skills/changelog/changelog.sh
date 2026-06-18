#!/usr/bin/env bash
# changelog.sh - Generate structured CHANGELOG.md from git history
# Usage: bash changelog.sh [output_file]
#
# Categorizes commits into Added/Fixed/Changed/Removed based on conventional
# commit prefixes. Fetches commits since the last git tag (or all commits
# if no tags exist).

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

# Ensure parent directory of OUTPUT exists
mkdir -p "$(dirname "$OUTPUT")" 2>/dev/null || true

# Get last tag (v* or *)
LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || echo "")"
if [ -z "$LAST_TAG" ]; then
    RANGE=""
    SECTION="Unreleased"
else
    RANGE="${LAST_TAG}..HEAD"
    SECTION="${LAST_TAG#v} - $(date +%Y-%m-%d)"
fi

# Initialize category files
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

for cat in Added Fixed Changed Removed; do
    : > "$TMPDIR/$cat"
done

# Parse commits
# Note: `|| [[ -n "$subject" ]]` ensures the last line is processed even if
# git log doesn't end with a newline.
git log $RANGE --pretty=format:"%s" 2>/dev/null | while IFS= read -r subject || [[ -n "$subject" ]]; do
    # Strip conventional commit prefix and colon
    msg="${subject#*: }"
    [ "$msg" = "$subject" ] && msg="$subject"  # No prefix

    # Categorize using bash case glob (more portable than [[ =~ ]] across bash versions).
    # Glob matches at start of string, so "feat" only matches "feat" / "Feat" / "feat(scope)" — not "feature".
    case "$subject" in
        feat*|Feat*)
            echo "- $msg" >> "$TMPDIR/Added"
            ;;
        fix*|Fix*)
            echo "- $msg" >> "$TMPDIR/Fixed"
            ;;
        BREAKING*|breaking*|revert*|Revert*)
            echo "- $msg" >> "$TMPDIR/Removed"
            ;;
        Remove*|remove*|Delete*|delete*)
            echo "- $msg" >> "$TMPDIR/Removed"
            ;;
        docs*|style*|refactor*|perf*|test*|chore*|build*|ci*)
            echo "- $msg" >> "$TMPDIR/Changed"
            ;;
        *)
            # No recognizable prefix -> Changed (fallback)
            echo "- $msg" >> "$TMPDIR/Changed"
            ;;
    esac
done

# Build CHANGELOG
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "## [$SECTION]"
    echo ""

    for cat in Added Fixed Changed Removed; do
        if [ -s "$TMPDIR/$cat" ]; then
            echo "### $cat"
            echo ""
            cat "$TMPDIR/$cat"
            echo ""
        fi
    done
} > "$OUTPUT"

COUNT=$(git log $RANGE --oneline 2>/dev/null | wc -l | tr -d ' ')
echo "CHANGELOG written to $OUTPUT ($COUNT commits processed)"
