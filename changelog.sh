#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Bounty: claude-builders-bounty Issue #1
# Usage: ./changelog.sh [options]
#   -t, --tag TAG     Generate changelog since TAG (default: last git tag)
#   -o, --output FILE Output file (default: CHANGELOG.md)
#   -r, --repo DIR    Repository path (default: current directory)
#   -n, --dry-run     Print to stdout instead of file
#   -h, --help        Show this help

set -euo pipefail

REPO_DIR="."
OUTPUT_FILE="CHANGELOG.md"
SINCE_TAG=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--tag)    SINCE_TAG="$2"; shift 2 ;;
        -o|--output) OUTPUT_FILE="$2"; shift 2 ;;
        -r|--repo)   REPO_DIR="$2"; shift 2 ;;
        -n|--dry-run) DRY_RUN=true; shift ;;
        -h|--help) sed -n '2,9p' "$0" | sed 's/^# //'; exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

cd "$REPO_DIR"

if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo "Error: not a git repository" >&2
    exit 1
fi

# Determine the starting tag
if [[ -z "$SINCE_TAG" ]]; then
    SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

# Build the git log range
if [[ -n "$SINCE_TAG" ]]; then
    LOG_RANGE="${SINCE_TAG}..HEAD"
    HEADER_VERSION="since ${SINCE_TAG}"
else
    LOG_RANGE="HEAD"
    HEADER_VERSION="all commits"
fi

TODAY=$(date +%Y-%m-%d)

# Categorize commits into temp files
TMPDIR=$(mktemp -d)
touch "$TMPDIR/added" "$TMPDIR/fixed" "$TMPDIR/changed" "$TMPDIR/removed" "$TMPDIR/docs" "$TMPDIR/other"

(git log --pretty=format:"%h|%s" "$LOG_RANGE" 2>/dev/null; echo "") | while IFS='|' read -r hash msg; do
    # Skip merge commits
    case "$msg" in
        Merge*) continue ;;
    esac

    # Categorize based on conventional commit prefix
    case "$msg" in
        feat:*|feat\ *|add:*|add\ *|feature:*|feature\ *)
            echo "$hash $msg" >> "$TMPDIR/added" ;;
        fix:*|fix\ *|bug:*|bug\ *|patch:*|patch\ *|hotfix:*|hotfix\ *)
            echo "$hash $msg" >> "$TMPDIR/fixed" ;;
        change:*|change\ *|update:*|update\ *|refactor:*|refactor\ *|rename:*|rename\ *|move:*|move\ *)
            echo "$hash $msg" >> "$TMPDIR/changed" ;;
        remove:*|remove\ *|delete:*|delete\ *|deprecate:*|deprecate\ *)
            echo "$hash $msg" >> "$TMPDIR/removed" ;;
        doc:*|doc\ *|docs:*|docs\ *|readme:*|readme\ *)
            echo "$hash $msg" >> "$TMPDIR/docs" ;;
        *)
            echo "$hash $msg" >> "$TMPDIR/other" ;;
    esac
done

# Build the changelog
CHANGELOG="# Changelog\n\n"
CHANGELOG="${CHANGELOG}## ${HEADER_VERSION} (${TODAY})\n\n"

format_section() {
    local title="$1"
    local file="$2"
    if [[ -s "$file" ]]; then
        CHANGELOG="${CHANGELOG}### ${title}\n\n"
        while IFS= read -r item; do
            local hash="${item%% *}"
            local desc="${item#* }"
            CHANGELOG="${CHANGELOG}- ${desc} (\`${hash}\`)\n"
        done < "$file"
        CHANGELOG="${CHANGELOG}\n"
    fi
}

format_section "Added" "$TMPDIR/added"
format_section "Fixed" "$TMPDIR/fixed"
format_section "Changed" "$TMPDIR/changed"
format_section "Removed" "$TMPDIR/removed"
format_section "Docs" "$TMPDIR/docs"
format_section "Other" "$TMPDIR/other"

# Cleanup
rm -rf "$TMPDIR"

# Output
if [[ "$DRY_RUN" == true ]]; then
    echo -e "$CHANGELOG"
else
    if [[ -f "$OUTPUT_FILE" ]] && grep -q "^## " "$OUTPUT_FILE"; then
        EXISTING=$(sed '1,/^## /d' "$OUTPUT_FILE")
        echo -e "$CHANGELOG" > "$OUTPUT_FILE"
        echo -e "$EXISTING" >> "$OUTPUT_FILE"
    else
        echo -e "$CHANGELOG" > "$OUTPUT_FILE"
    fi
    echo "Changelog written to ${OUTPUT_FILE}"
fi
