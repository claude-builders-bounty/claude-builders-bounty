#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [OUTPUT_FILE]
#
# Fetches commits since the last git tag and auto-categorizes them into:
# Added, Fixed, Changed, Removed
#
# Supports conventional commit prefixes and keyword-based fallback categorization.

set -euo pipefail

OUTPUT_FILE="${1:-CHANGELOG.md}"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
    echo "Error: Not inside a git repository." >&2
    exit 1
}

cd "$REPO_ROOT"

# --- Resolve the latest tag (if any) ---
LATEST_TAG=""
if git describe --tags --abbrev=0 HEAD &>/dev/null; then
    LATEST_TAG=$(git describe --tags --abbrev=0 HEAD)
fi

# --- Collect commits ---
if [[ -n "$LATEST_TAG" ]]; then
    RANGE="${LATEST_TAG}..HEAD"
    TAG_DATE=$(git log -1 --format='%as' "$LATEST_TAG")
else
    RANGE="HEAD"
    TAG_DATE=""
fi

# Get commits in reverse chronological order (skip merge commits)
mapfile -t COMMITS < <(git log "$RANGE" --no-merges --pretty=format:'%H|%s|%as' --reverse 2>/dev/null)

if [[ ${#COMMITS[@]} -eq 0 ]]; then
    echo "No new commits found since ${LATEST_TAG:-the beginning}." >&2
    # Write minimal changelog
    cat > "$OUTPUT_FILE" <<EOF
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

No changes since ${LATEST_TAG:-initial commit}.
EOF
    echo "Wrote $OUTPUT_FILE (no new changes)."
    exit 0
fi

# --- Categorize commits ---
declare -A CATEGORY_MAP
CATEGORY_MAP=(
    [Added]=""
    [Fixed]=""
    [Changed]=""
    [Removed]=""
)

categorize_commit() {
    local subject="$1"
    local lower
    lower=$(echo "$subject" | tr '[:upper:]' '[:lower:]')

    # Conventional commit prefix detection
    if [[ "$lower" =~ ^(feat|feature)(\(.+\))?!?:\ .+ ]]; then
        echo "Added"
    elif [[ "$lower" =~ ^(fix|bugfix|hotfix)(\(.+\))?!?:\ .+ ]]; then
        echo "Fixed"
    elif [[ "$lower" =~ ^(refactor|chore|build|ci|perf|style)(\(.+\))?!?:\ .+ ]]; then
        echo "Changed"
    elif [[ "$lower" =~ ^(remove|delete|deprecate)(\(.+\))?!?:\ .+ ]]; then
        echo "Removed"
    elif [[ "$lower" =~ ^(docs|doc|documentation)(\(.+\))?!?:\ .+ ]]; then
        echo "Changed"
    elif [[ "$lower" =~ ^(test|tests|testing)(\(.+\))?!?:\ .+ ]]; then
        echo "Changed"
    # Keyword-based fallback
    elif [[ "$lower" =~ (add|new|create|introduce|implement|support) ]]; then
        echo "Added"
    elif [[ "$lower" =~ (fix|bug|patch|resolve|correct|repair|issue) ]]; then
        echo "Fixed"
    elif [[ "$lower" =~ (remove|delete|deprecat|drop|eliminat) ]]; then
        echo "Removed"
    elif [[ "$lower" =~ (update|change|refactor|improve|enhance|rename|move|migrat|upgrad|bump|clean|adjust) ]]; then
        echo "Changed"
    else
        echo "Changed"
    fi
}

for entry in "${COMMITS[@]}"; do
    IFS='|' read -r hash subject date <<< "$entry"
    short_hash="${hash:0:7}"
    category=$(categorize_commit "$subject")
    CATEGORY_MAP[$category]+="- ${subject} (\`${short_hash}\`) [${date}]"$'\n'
done

# --- Build the output ---
DATE_TODAY=$(date +%Y-%m-%d)
VERSION_LABEL="Unreleased"
if [[ -n "$LATEST_TAG" ]]; then
    VERSION_LABEL="Since ${LATEST_TAG}"
fi

{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "## [${VERSION_LABEL}] — ${DATE_TODAY}"
    echo ""

    for cat in Added Fixed Changed Removed; do
        content="${CATEGORY_MAP[$cat]}"
        if [[ -n "$content" ]]; then
            echo "### ${cat}"
            echo ""
            echo "$content"
        fi
    done

    # Append previous tag section if available
    if [[ -n "$LATEST_TAG" ]]; then
        echo "---"
        echo ""
        echo "_Previous release: ${LATEST_TAG} (${TAG_DATE})_"
        echo ""
    fi
} > "$OUTPUT_FILE"

# --- Summary ---
added_count=$(echo "${CATEGORY_MAP[Added]}" | grep -c '^- ' 2>/dev/null || echo 0)
fixed_count=$(echo "${CATEGORY_MAP[Fixed]}" | grep -c '^- ' 2>/dev/null || echo 0)
changed_count=$(echo "${CATEGORY_MAP[Changed]}" | grep -c '^- ' 2>/dev/null || echo 0)
removed_count=$(echo "${CATEGORY_MAP[Removed]}" | grep -c '^- ' 2>/dev/null || echo 0)

echo "CHANGELOG generated: ${OUTPUT_FILE}"
echo "  Added: ${added_count}, Fixed: ${fixed_count}, Changed: ${changed_count}, Removed: ${removed_count}"
