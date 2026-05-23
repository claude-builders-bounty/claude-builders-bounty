#!/usr/bin/env bash
# changelog.sh — Auto-generate CHANGELOG.md from git history
# Usage: bash changelog.sh [--output CHANGELOG.md]

set -euo pipefail

OUTPUT="${2:-CHANGELOG.md}"

# Find the latest tag, default to first commit if no tags
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)

echo "# Changelog" > "$OUTPUT"
echo "" >> "$OUTPUT"

# Generate per-tag/release sections
if git describe --tags --abbrev=0 &>/dev/null; then
    # List tags in reverse chronological order
    git tag --sort=-v:refname 2>/dev/null | while read -r tag; do
        prev_tag=$(git tag --sort=-v:refname | grep -A1 "$tag" | tail -1)
        if [ "$prev_tag" = "$tag" ]; then
            prev_tag=""
        fi
        
        echo "## [${tag}]" >> "$OUTPUT"
        echo "" >> "$OUTPUT"
        generate_section "$prev_tag" "$tag" "$OUTPUT"
    done
    
    # Commits since the last tag (unreleased)
    LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)
    echo "## [Unreleased]" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    generate_section "$LAST_TAG" "HEAD" "$OUTPUT"
else
    # No tags — show all commits as unreleased
    echo "## [Unreleased]" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    generate_section "" "HEAD" "$OUTPUT"
fi

echo "✅ Generated $OUTPUT"

# Helper: generate categorized section
generate_section() {
    local from="$1" to="$2" outfile="$3"
    
    if [ -n "$from" ]; then
        range="${from}..${to}"
    else
        range="${to}"
    fi
    
    # Parse commits by conventional commit type
    while IFS=$'\n' read -r commit; do
        [ -z "$commit" ] && continue
        local msg="${commit#* }"  # strip hash
        if [[ "$msg" =~ ^feat[\(]?[^)]*[\)]?: ]]; then
            echo "- ${msg#*: }" >> "$outfile"
        fi
    done < <(git log "$range" --oneline --no-decorate 2>/dev/null | grep -E '^[a-f0-9]+ (feat|fix|docs|refactor|chore|perf|test)')
    
    # If empty, note that
    if [ -z "$(git log "$range" --oneline 2>/dev/null)" ]; then
        echo "- Initial release" >> "$outfile"
    fi
    
    echo "" >> "$outfile"
}
