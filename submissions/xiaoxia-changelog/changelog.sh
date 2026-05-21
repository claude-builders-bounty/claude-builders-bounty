#!/usr/bin/env bash
# CHANGELOG Generator — generates structured CHANGELOG.md from git history
# Bounty #1: $50 — claude-builders-bounty
set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"
SINCE_TAG="${2:-$(git describe --tags --abbrev=0 2>/dev/null || echo '')}"
REPO_URL="${3:-}"

echo "# Changelog" > "$OUTPUT"
echo "" >> "$OUTPUT"
echo "Generated: $(date -u +'%Y-%m-%dT%H:%M:%SZ')" >> "$OUTPUT"
echo "" >> "$OUTPUT"

# Get commits since last tag (or all commits if no tag)
if [ -n "$SINCE_TAG" ]; then
    echo "> Since tag: \`$SINCE_TAG\`" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    COMMITS=$(git log "${SINCE_TAG}..HEAD" --pretty=format:"%H|%s|%an|%ad" --date=short)
else
    COMMITS=$(git log --pretty=format:"%H|%s|%an|%ad" --date=short)
fi

# Categorize commits
declare -A CATEGORIES
CATEGORIES["Added"]=""
CATEGORIES["Fixed"]=""
CATEGORIES["Changed"]=""
CATEGORIES["Removed"]=""
CATEGORIES["Security"]=""
CATEGORIES["Other"]=""

while IFS='|' read -r hash subject author date; do
    [ -z "$hash" ] && continue
    
    commit_link=""
    if [ -n "$REPO_URL" ]; then
        commit_link=" ([${hash:0:7}](${REPO_URL}/commit/${hash}))"
    else
        commit_link=" (\`${hash:0:7}\`)"
    fi
    
    line="- ${subject}${commit_link} (@${author})"
    
    # Categorize by conventional commit prefix
    lower_subject=$(echo "$subject" | tr '[:upper:]' '[:lower:]')
    case "$lower_subject" in
        feat:*|add:*|feature:*)    CATEGORIES["Added"]+="$line"$'\n' ;;
        fix:*|bug:*|patch:*)       CATEGORIES["Fixed"]+="$line"$'\n' ;;
        refactor:*|change:*|perf:*)CATEGORIES["Changed"]+="$line"$'\n' ;;
        remove:*|revert:*|drop:*)  CATEGORIES["Removed"]+="$line"$'\n' ;;
        security:*|sec:*|vuln:*)   CATEGORIES["Security"]+="$line"$'\n' ;;
        *)                         CATEGORIES["Other"]+="$line"$'\n' ;;
    esac
done <<< "$COMMITS"

# Write sections (only non-empty)
for section in "Added" "Fixed" "Changed" "Removed" "Security" "Other"; do
    content="${CATEGORIES[$section]}"
    if [ -n "$content" ]; then
        echo "## $section" >> "$OUTPUT"
        echo "$content" | sort -u >> "$OUTPUT"
        echo "" >> "$OUTPUT"
    fi
done

echo "CHANGELOG written to $OUTPUT ($(wc -l < "$OUTPUT") lines)"
