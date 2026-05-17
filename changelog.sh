#!/usr/bin/env bash
# changelog.sh — Generate structured CHANGELOG.md from git history
# Usage: bash changelog.sh [--since TAG] [--output FILE]
set -euo pipefail

OUTPUT="${PWD}/CHANGELOG.md"
SINCE_TAG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --since) SINCE_TAG="$2"; shift 2 ;;
        --output) OUTPUT="$2"; shift 2 ;;
        *) echo "Usage: bash changelog.sh [--since TAG] [--output FILE]"; exit 1 ;;
    esac
done

# Auto-detect last tag if not specified
if [[ -z "$SINCE_TAG" ]]; then
    SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

echo "# Changelog" > "$OUTPUT"
echo "" >> "$OUTPUT"

# Determine date range
if [[ -n "$SINCE_TAG" ]]; then
    TAG_DATE=$(git log -1 --format=%ai "$SINCE_TAG" 2>/dev/null || echo "unknown")
    echo "## $(date +%Y-%m-%d) — since $SINCE_TAG ($TAG_DATE)" >> "$OUTPUT"
    RANGE="${SINCE_TAG}..HEAD"
else
    echo "## $(date +%Y-%m-%d) — all commits" >> "$OUTPUT"
    RANGE="HEAD"
fi
echo "" >> "$OUTPUT"

# Extract categorized commits
commits=$(git log "$RANGE" --no-merges --format="%s" 2>/dev/null)

ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
OTHER=()

while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    msg=$(echo "$line" | sed 's/^[^a-zA-Z]*//')
    if   echo "$msg" | grep -qiE '^(add|feat|implement|introduce|create|new)'; then ADDED+=("$msg")
    elif echo "$msg" | grep -qiE '^(fix|patch|resolve|bug|hotfix|correct)'; then FIXED+=("$msg")
    elif echo "$msg" | grep -qiE '^(change|update|refactor|improve|enhance|tweak|modify|adjust)'; then CHANGED+=("$msg")
    elif echo "$msg" | grep -qiE '^(remove|delete|drop|deprecate|retire)'; then REMOVED+=("$msg")
    else OTHER+=("$msg")
    fi
done <<< "$commits"

# Output sections
write_section() {
    local title="$1"; shift
    local -a items=("$@")
    if [[ ${#items[@]} -gt 0 ]]; then
        echo "### $title" >> "$OUTPUT"
        echo "" >> "$OUTPUT"
        for item in "${items[@]}"; do
            echo "- $item" >> "$OUTPUT"
        done
        echo "" >> "$OUTPUT"
    fi
}

write_section "Added" "${ADDED[@]}"
write_section "Fixed" "${FIXED[@]}"
write_section "Changed" "${CHANGED[@]}"
write_section "Removed" "${REMOVED[@]}"

if [[ ${#OTHER[@]} -gt 0 ]]; then
    echo "### Other" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    for item in "${OTHER[@]}"; do
        echo "- $item" >> "$OUTPUT"
    done
    echo "" >> "$OUTPUT"
fi

echo "✔ CHANGELOG.md generated ($(wc -l < "$OUTPUT") lines)"
