#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
#
# Usage:
#   bash changelog.sh [output_file] [tag_prefix]
#
# Examples:
#   bash changelog.sh                    # → CHANGELOG.md
#   bash changelog.sh docs/CHANGELOG.md  # → docs/CHANGELOG.md
#   bash changelog.sh CHANGELOG.md v     # tags like v1.0.0

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
TAG_PREFIX="${2:-}"

# Get the latest tag (with optional prefix)
if [ -n "$TAG_PREFIX" ]; then
    LATEST_TAG=$(git tag --sort=-v:refname | grep "^${TAG_PREFIX}" | head -1)
else
    LATEST_TAG=$(git tag --sort=-v:refname | head -1)
fi

if [ -z "$LATEST_TAG" ]; then
    RANGE="HEAD"
    HEADER="# Changelog\n\n## [Unreleased]\n"
else
    RANGE="${LATEST_TAG}..HEAD"
    TAG_DATE=$(git log -1 --format=%ai "$LATEST_TAG" | cut -d' ' -f1)
    HEADER="# Changelog\n\n## [Unreleased] (since ${LATEST_TAG} — ${TAG_DATE})\n"
fi

# Collect commits
COMMITS=$(git log --pretty=format:"%H|||%s|||%an|||%ai" "$RANGE" 2>/dev/null || true)

if [ -z "$COMMITS" ]; then
    echo -e "# Changelog\n\nNo changes since ${LATEST_TAG:-initial commit}." > "$OUTPUT"
    echo "✅ Generated $OUTPUT (no changes found)"
    exit 0
fi

# Categorize commits
declare -a ADDED=() FIXED=() CHANGED=() REMOVED=() OTHER=()

while IFS= read -r line; do
    hash=$(echo "$line" | cut -d'|' -f1)
    subject_clean=$(echo "$line" | awk -F'\\|\\|\\|' '{print $2}')
    short_hash="${hash:0:7}"
    entry="- ${subject_clean} (\`${short_hash}\`)"

    lower_subject=$(echo "$subject_clean" | tr '[:upper:]' '[:lower:]')

    case "$lower_subject" in
        add*|feat*|new*|implement*|create*|support*|initial*)
            ADDED+=("$entry") ;;
        fix*|bug*|resolve*|patch*|correct*|repair*)
            FIXED+=("$entry") ;;
        change*|update*|refactor*|improve*|optimize*|enhance*|rename*|move*|restructur*)
            CHANGED+=("$entry") ;;
        remove*|delete*|deprecat*|drop*|eliminat*)
            REMOVED+=("$entry") ;;
        doc*|readme*|comment*)
            CHANGED+=("$entry") ;;
        test*|ci*|build*|chore*|bump*|release*|merge*)
            OTHER+=("$entry") ;;
        revert*)
            FIXED+=("$entry") ;;
        *)
            OTHER+=("$entry") ;;
    esac
done <<< "$COMMITS"

# Generate output
{
    echo -e "$HEADER"

    if [ ${#ADDED[@]} -gt 0 ]; then
        echo "### Added"
        printf '%s\n' "${ADDED[@]}"
        echo ""
    fi

    if [ ${#FIXED[@]} -gt 0 ]; then
        echo "### Fixed"
        printf '%s\n' "${FIXED[@]}"
        echo ""
    fi

    if [ ${#CHANGED[@]} -gt 0 ]; then
        echo "### Changed"
        printf '%s\n' "${CHANGED[@]}"
        echo ""
    fi

    if [ ${#REMOVED[@]} -gt 0 ]; then
        echo "### Removed"
        printf '%s\n' "${REMOVED[@]}"
        echo ""
    fi

    if [ ${#OTHER[@]} -gt 0 ]; then
        echo "### Other"
        printf '%s\n' "${OTHER[@]}"
        echo ""
    fi
} > "$OUTPUT"

TOTAL=$(( ${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} + ${#OTHER[@]} ))
echo "✅ Generated $OUTPUT ($TOTAL commits categorized)"
echo "   Added: ${#ADDED[@]} | Fixed: ${#FIXED[@]} | Changed: ${#CHANGED[@]} | Removed: ${#REMOVED[@]} | Other: ${#OTHER[@]}"
