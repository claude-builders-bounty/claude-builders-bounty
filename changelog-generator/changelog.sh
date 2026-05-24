#!/usr/bin/env bash
set -euo pipefail

# ============================================
# CHANGELOG Generator
# Auto-generate structured CHANGELOG.md from git history
# ============================================

OUTPUT="CHANGELOG.md"
SINCE=""
DRY_RUN=false

usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Generate a structured CHANGELOG.md from git commits since the last tag.

Options:
  --output FILE   Output file (default: CHANGELOG.md)
  --since TAG     Start from a specific tag (default: latest tag)
  --dry-run       Print to stdout instead of writing file
  --help          Show this help

Example:
  $0
  $0 --since v1.0.0 --output docs/CHANGELOG.md
EOF
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --output) OUTPUT="$2"; shift 2 ;;
        --since)  SINCE="$2"; shift 2 ;;
        --dry-run) DRY_RUN=true; shift ;;
        --help)   usage ;;
        *) echo "Unknown option: $1"; usage ;;
    esac
done

# Must be in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not in a git repository."
    exit 1
fi

# Determine the starting point
if [[ -z "$SINCE" ]]; then
    SINCE=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [[ -z "$SINCE" ]]; then
        echo "No git tags found. Using first commit as starting point."
        SINCE=$(git rev-list --max-parents=0 HEAD)
    fi
fi

TODAY=$(date +%Y-%m-%d)

# Determine next version: suggest a semver bump based on commit types
NEXT_VERSION="Unreleased"
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [[ -n "$LATEST_TAG" ]]; then
    # Strip leading 'v' for parsing
    BASE="${LATEST_TAG#v}"
    IFS='.' read -r MAJOR MINOR PATCH <<< "$BASE"
    MAJOR=${MAJOR:-0}; MINOR=${MINOR:-0}; PATCH=${PATCH:-0}
    # Suggest a minor bump by default; major if breaking changes detected
    if git log "$SINCE..HEAD" --pretty=format:"%s" --no-merges 2>/dev/null | grep -qiE '!.+:'; then
        NEXT_VERSION="v$((MAJOR + 1)).0.0"
    else
        NEXT_VERSION="v$MAJOR.$((MINOR + 1)).0"
    fi
fi

echo "Generating changelog from: $SINCE"

# Collect commits
COMMITS=$(git log "$SINCE..HEAD" --pretty=format:"%s" --no-merges 2>/dev/null || echo "")

# Categorization
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""

while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    # Categorize by conventional commit type prefix
    if echo "$line" | grep -qiE '^(feat|add|new|implement)(\(.+\))?!?:'; then
        ADDED+="  - $line"$'\n'
    elif echo "$line" | grep -qiE '^(fix|bug|patch|hotfix|repair)(\(.+\))?!?:'; then
        FIXED+="  - $line"$'\n'
    elif echo "$line" | grep -qiE '^(remove|drop|delete|deprecate|rm)(\(.+\))?!?:'; then
        REMOVED+="  - $line"$'\n'
    else
        CHANGED+="  - $line"$'\n'
    fi
done <<< "$COMMITS"

# Build changelog content
CONTENT="# Changelog\n\n## [$NEXT_VERSION] - $TODAY\n"

if [[ -n "$ADDED" ]]; then
    CONTENT+="\n### Added\n\n$ADDED"
fi
if [[ -n "$FIXED" ]]; then
    CONTENT+="\n### Fixed\n\n$FIXED"
fi
if [[ -n "$CHANGED" ]]; then
    CONTENT+="\n### Changed\n\n$CHANGED"
fi
if [[ -n "$REMOVED" ]]; then
    CONTENT+="\n### Removed\n\n$REMOVED"
fi

if [[ -z "$ADDED$FIXED$CHANGED$REMOVED" ]]; then
    CONTENT+="\n_No changes since $SINCE._\n"
fi

# Output
if $DRY_RUN; then
    printf '%b\n' "$CONTENT"
else
    # If file exists, prepend; otherwise create
    if [[ -f "$OUTPUT" ]]; then
        EXISTING=$(cat "$OUTPUT" 2>/dev/null || echo "")
        printf '%b\n\n%s\n' "$CONTENT" "$EXISTING" > "$OUTPUT"
        echo "Prepended to existing $OUTPUT"
    else
        printf '%b\n' "$CONTENT" > "$OUTPUT"
        echo "Created $OUTPUT"
    fi
fi

# Summary
ADDED_COUNT=$(echo "$ADDED" | grep -cE '^\s*- ' 2>/dev/null || true)
FIXED_COUNT=$(echo "$FIXED" | grep -cE '^\s*- ' 2>/dev/null || true)
CHANGED_COUNT=$(echo "$CHANGED" | grep -cE '^\s*- ' 2>/dev/null || true)
REMOVED_COUNT=$(echo "$REMOVED" | grep -cE '^\s*- ' 2>/dev/null || true)
ADDED_COUNT=${ADDED_COUNT:-0}
FIXED_COUNT=${FIXED_COUNT:-0}
CHANGED_COUNT=${CHANGED_COUNT:-0}
REMOVED_COUNT=${REMOVED_COUNT:-0}
TOTAL=$((ADDED_COUNT + FIXED_COUNT + CHANGED_COUNT + REMOVED_COUNT))

echo "Done! $TOTAL commits categorized:"
echo "  Added:   $ADDED_COUNT"
echo "  Fixed:   $FIXED_COUNT"
echo "  Changed: $CHANGED_COUNT"
echo "  Removed: $REMOVED_COUNT"
