#!/usr/bin/env bash
#
# generate-changelog.sh — Generate a structured CHANGELOG.md from git history
#
# Usage:
#   bash generate-changelog.sh                  # Since last tag
#   bash generate-changelog.sh v1.0.0           # Since specific tag
#   bash generate-changelog.sh v1.0.0 v2.0.0    # Between two tags
#   bash generate-changelog.sh --all             # Full history
#
# Categorizes commits into: Added, Fixed, Changed, Removed, Security, Performance
# Supports Conventional Commits (feat:, fix:, etc.) and keyword detection.
#

set -euo pipefail

VERSION_FROM="${1:-}"
VERSION_TO="${2:-HEAD}"
OUTPUT_FILE="CHANGELOG.md"
DATE=$(date +%Y-%m-%d)

# ---------- Resolve version range ----------

if [[ "$VERSION_FROM" == "--all" ]]; then
    RANGE=""
    RANGE_LABEL="Full History"
elif [[ -z "$VERSION_FROM" ]]; then
    # Auto-detect last tag
    LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
    if [[ -z "$LAST_TAG" ]]; then
        RANGE=""
        RANGE_LABEL="Full History (no tags found)"
    else
        RANGE="${LAST_TAG}..${VERSION_TO}"
        RANGE_LABEL="Since ${LAST_TAG}"
    fi
else
    if [[ "$VERSION_TO" == "HEAD" ]]; then
        RANGE="${VERSION_FROM}..HEAD"
        RANGE_LABEL="Since ${VERSION_FROM}"
    else
        RANGE="${VERSION_FROM}..${VERSION_TO}"
        RANGE_LABEL="${VERSION_FROM} → ${VERSION_TO}"
    fi
fi

echo "Generating CHANGELOG ($RANGE_LABEL)..."

# ---------- Collect commits ----------

if [[ -z "$RANGE" ]]; then
    COMMITS=$(git log --pretty=format:"%H|||%s|||%an|||%ad" --date=short 2>/dev/null || echo "")
else
    COMMITS=$(git log "$RANGE" --pretty=format:"%H|||%s|||%an|||%ad" --date=short 2>/dev/null || echo "")
fi

if [[ -z "$COMMITS" ]]; then
    echo "No commits found for range: $RANGE_LABEL"
    exit 0
fi

# ---------- Categorize ----------

ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
SECURITY=""
PERFORMANCE=""
OTHER=""

while IFS= read -r line; do
    HASH=$(echo "$line" | awk -F'\\|\\|\\|' '{print $1}')
    MSG=$(echo "$line" | awk -F'\\|\\|\\|' '{print $2}')
    AUTHOR=$(echo "$line" | awk -F'\\|\\|\\|' '{print $3}')
    COMMIT_DATE=$(echo "$line" | awk -F'\\|\\|\\|' '{print $4}')
    SHORT_HASH="${HASH:0:7}"

    # Skip merge commits
    [[ "$MSG" =~ ^Merge ]] && continue

    # Categorize by Conventional Commits prefix or keywords
    MSG_LOWER=$(echo "$MSG" | tr '[:upper:]' '[:lower:]')
    ENTRY="- ${MSG} (\`${SHORT_HASH}\` by ${AUTHOR}, ${COMMIT_DATE})"

    ADDED_RE="^feat|^add |^add:|added |new |implement|introduce"
    FIXED_RE="^fix|^bug|fixed |bugfix|hotfix|patch|resolve"
    REMOVED_RE="^remove|^delete|deprecated|drop |removed "
    SECURITY_RE="^security|^vuln|cve-|xss|injection"
    PERF_RE="^perf|performance|optimize|speed|cache|faster"
    CHANGED_RE="^refactor|^chore|^style|^docs|^test|^ci|^build|^change|update|modify|improve|enhance|adjust"

    if [[ "$MSG_LOWER" =~ $ADDED_RE ]]; then
        ADDED="${ADDED}${ENTRY}\n"
    elif [[ "$MSG_LOWER" =~ $FIXED_RE ]]; then
        FIXED="${FIXED}${ENTRY}\n"
    elif [[ "$MSG_LOWER" =~ $REMOVED_RE ]]; then
        REMOVED="${REMOVED}${ENTRY}\n"
    elif [[ "$MSG_LOWER" =~ $SECURITY_RE ]]; then
        SECURITY="${SECURITY}${ENTRY}\n"
    elif [[ "$MSG_LOWER" =~ $PERF_RE ]]; then
        PERFORMANCE="${PERFORMANCE}${ENTRY}\n"
    elif [[ "$MSG_LOWER" =~ $CHANGED_RE ]]; then
        CHANGED="${CHANGED}${ENTRY}\n"
    else
        OTHER="${OTHER}${ENTRY}\n"
    fi
done <<< "$COMMITS"

# ---------- Generate CHANGELOG.md ----------

{
    echo "# Changelog"
    echo ""
    echo "## [$RANGE_LABEL] — $DATE"
    echo ""

    if [[ -n "$ADDED" ]]; then
        echo "### Added"
        echo -e "$ADDED"
    fi

    if [[ -n "$FIXED" ]]; then
        echo "### Fixed"
        echo -e "$FIXED"
    fi

    if [[ -n "$CHANGED" ]]; then
        echo "### Changed"
        echo -e "$CHANGED"
    fi

    if [[ -n "$REMOVED" ]]; then
        echo "### Removed"
        echo -e "$REMOVED"
    fi

    if [[ -n "$SECURITY" ]]; then
        echo "### Security"
        echo -e "$SECURITY"
    fi

    if [[ -n "$PERFORMANCE" ]]; then
        echo "### Performance"
        echo -e "$PERFORMANCE"
    fi

    if [[ -n "$OTHER" ]]; then
        echo "### Other"
        echo -e "$OTHER"
    fi

    # Stats footer
    TOTAL=$(echo "$COMMITS" | wc -l | tr -d ' ')
    AUTHORS=$(echo "$COMMITS" | awk -F'\\|\\|\\|' '{print $3}' | sort -u | wc -l | tr -d ' ')
    echo "---"
    echo ""
    echo "_${TOTAL} commits by ${AUTHORS} contributor(s). Generated on ${DATE}._"

} > "$OUTPUT_FILE"

echo "Done! Written to $OUTPUT_FILE"
echo ""
echo "--- Preview ---"
head -40 "$OUTPUT_FILE"
