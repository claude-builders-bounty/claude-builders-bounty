#!/usr/bin/env bash
# changelog.sh — Auto-generate structured CHANGELOG.md from git history
# Requirements: git, bash
# Usage: ./changelog.sh [output_file]

set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
REPO_URL=""

# Try to get the remote URL
if git remote get-url origin >/dev/null 2>&1; then
    REPO_URL="$(git remote get-url origin)"
    # Convert SSH URL to HTTPS for links
    REPO_URL="${REPO_URL/git@github.com:/https://github.com/}"
    REPO_URL="${REPO_URL%.git}"
fi

# Get the last tag, or use empty
LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || echo "")"

# Build commit range
if [ -n "$LAST_TAG" ]; then
    COMMIT_RANGE="${LAST_TAG}..HEAD"
else
    COMMIT_RANGE="HEAD"
fi

# Categorization patterns
added_patterns="^(feat|add|introduce|implement|create|new)"
fixed_patterns="^(fix|bug|hotfix|patch|repair|correct)"
changed_patterns="^(update|refactor|perf|optimize|improve|enhance|change|modify|chore|deps|upgrade|migrate|style|docs|test|ci)"
removed_patterns="^(remove|delete|drop|deprecat|revert|undo|clean|cleanup)"

declare -a added=()
declare -a fixed=()
declare -a changed=()
declare -a removed=()
declare -a other=()

# Read commits since last tag
while IFS='|' read -r hash subject author date; do
    # Skip merge commits and changelog commits
    [[ "$subject" == *"Merge"* ]] && continue
    [[ "$subject" == *"changelog"* ]] && continue
    [[ "$subject" == *"CHANGELOG"* ]] && continue

    # Normalize subject for matching
    lower_subject="${subject,,}"

    if [[ "$lower_subject" =~ $added_patterns ]]; then
        added+=("$hash|$subject|$author|$date")
    elif [[ "$lower_subject" =~ $fixed_patterns ]]; then
        fixed+=("$hash|$subject|$author|$date")
    elif [[ "$lower_subject" =~ $changed_patterns ]]; then
        changed+=("$hash|$subject|$author|$date")
    elif [[ "$lower_subject" =~ $removed_patterns ]]; then
        removed+=("$hash|$subject|$author|$date")
    else
        other+=("$hash|$subject|$author|$date")
    fi
done < <(git log --format="%H|%s|%an|%ad" --date=short "$COMMIT_RANGE" 2>/dev/null || true)

# Helper to print a category
print_category() {
    local title="$1"
    shift
    local commits=("$@")
    if [ ${#commits[@]} -eq 0 ]; then
        return
    fi
    echo "### $title"
    for entry in "${commits[@]}"; do
        IFS='|' read -r hash subject author date <<< "$entry"
        if [ -n "$REPO_URL" ]; then
            echo "- $subject ([\`$hash\`]($REPO_URL/commit/$hash)) — $author, $date"
        else
            echo "- $subject (\`$hash\`) — $author, $date"
        fi
    done
    echo ""
}

# Build the changelog
cat > "$OUTPUT" << 'EOF'
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

EOF

print_category "Added" "${added[@]}" >> "$OUTPUT"
print_category "Fixed" "${fixed[@]}" >> "$OUTPUT"
print_category "Changed" "${changed[@]}" >> "$OUTPUT"
print_category "Removed" "${removed[@]}" >> "$OUTPUT"

if [ ${#other[@]} -gt 0 ]; then
    echo "### Other" >> "$OUTPUT"
    for entry in "${other[@]}"; do
        IFS='|' read -r hash subject author date <<< "$entry"
        if [ -n "$REPO_URL" ]; then
            echo "- $subject ([\`$hash\`]($REPO_URL/commit/$hash)) — $author, $date" >> "$OUTPUT"
        else
            echo "- $subject (\`$hash\`) — $author, $date" >> "$OUTPUT"
        fi
    done
    echo "" >> "$OUTPUT"
fi

echo "✅ Changelog written to: $OUTPUT"
