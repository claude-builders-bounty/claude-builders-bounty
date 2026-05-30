#!/usr/bin/env bash
# changelog.sh — Generate structured CHANGELOG.md from git history
# Usage: bash changelog.sh [output_file] [--since TAG]
set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
SINCE_TAG="${2:-}"

# Handle --since flag
if [[ "$OUTPUT" == "--since" ]] && [[ -n "${2:-}" ]]; then
    SINCE_TAG="$2"
    OUTPUT="CHANGELOG.md"
fi

# Get the latest tag if --since not provided
if [[ -z "$SINCE_TAG" ]]; then
    SINCE_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

# Build git log range
if [[ -n "$SINCE_TAG" ]]; then
    RANGE="${SINCE_TAG}..HEAD"
    echo "📋 Generating changelog since ${SINCE_TAG}..."
else
    RANGE="HEAD~50..HEAD"
    SINCE_TAG="(no tags found)"
    echo "📋 Generating changelog (last 50 commits)..."
fi

# Collect commits: hash|subject
COMMITS=$(git log "$RANGE" --pretty=format:"%h|%s" --no-merges 2>/dev/null || true)

if [[ -z "$COMMITS" ]]; then
    echo "⚠️  No commits found since $SINCE_TAG"
    exit 0
fi

# Categorize
ADDED=""
FIXED=""
CHANGED=""
REMOVED=""
OTHER=""

while IFS='|' read -r hash subject; do
    [[ -z "$hash" ]] && continue
    lower=$(echo "$subject" | tr '[:upper:]' '[:lower:]')
    
    entry="- ${subject} (\`${hash}\`)"
    
    if [[ "$lower" =~ ^feat ]] || [[ "$lower" =~ ^add ]] || [[ "$lower" =~ ^new\  ]] || [[ "$lower" =~ ^implement ]]; then
        ADDED="${ADDED}${entry}\n"
    elif [[ "$lower" =~ ^fix ]] || [[ "$lower" =~ ^bug ]] || [[ "$lower" =~ ^patch ]] || [[ "$lower" =~ ^hotfix ]]; then
        FIXED="${FIXED}${entry}\n"
    elif [[ "$lower" =~ ^remove ]] || [[ "$lower" =~ ^delete ]] || [[ "$lower" =~ ^drop ]] || [[ "$lower" =~ ^deprecate ]]; then
        REMOVED="${REMOVED}${entry}\n"
    elif [[ "$lower" =~ ^refactor ]] || [[ "$lower" =~ ^chore ]] || [[ "$lower" =~ ^update ]] || [[ "$lower" =~ ^change ]] || [[ "$lower" =~ ^improve ]] || [[ "$lower" =~ ^bump ]]; then
        CHANGED="${CHANGED}${entry}\n"
    else
        OTHER="${OTHER}${entry}\n"
    fi
done <<< "$COMMITS"

# Build output
DATE=$(date +%Y-%m-%d)
{
    echo "## [Unreleased] — ${DATE}"
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
    if [[ -n "$OTHER" ]]; then
        echo "### Other"
        echo -e "$OTHER"
    fi
} > "$OUTPUT"

TOTAL=$(echo "$COMMITS" | wc -l | tr -d ' ')
echo "✅ Generated ${OUTPUT} (${TOTAL} commits) since ${SINCE_TAG}"
