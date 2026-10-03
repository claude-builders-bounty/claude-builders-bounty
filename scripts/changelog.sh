#!/usr/bin/env bash
# Generates a structured CHANGELOG.md from git history since the last tag.

set -euo pipefail

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -z "$LAST_TAG" ]; then
    COMMITS=$(git log --pretty=format:"%s" --no-merges)
    TAG_TITLE="Unreleased (All History)"
else
    COMMITS=$(git log "${LAST_TAG}..HEAD" --pretty=format:"%s" --no-merges)
    TAG_TITLE="Unreleased (Since ${LAST_TAG})"
fi

ADDED=()
FIXED=()
CHANGED=()
REMOVED=()
OTHER=()

while IFS= read -r line; do
    [ -z "$line" ] && continue
    if [[ "$line" =~ ^(feat|add|feature)(\(.*\))?:\ (.*) ]]; then
        ADDED+=("- ${BASH_REMATCH[3]}")
    elif [[ "$line" =~ ^(fix|bug)(\(.*\))?:\ (.*) ]]; then
        FIXED+=("- ${BASH_REMATCH[3]}")
    elif [[ "$line" =~ ^(change|refactor|perf|style)(\(.*\))?:\ (.*) ]]; then
        CHANGED+=("- ${BASH_REMATCH[3]}")
    elif [[ "$line" =~ ^(remove|deprecate)(\(.*\))?:\ (.*) ]]; then
        REMOVED+=("- ${BASH_REMATCH[3]}")
    else
        OTHER+=("- $line")
    fi
done <<< "$COMMITS"

OUTPUT="## [${TAG_TITLE}] - $(date +%Y-%m-%d)\n\n"

if [ ${#ADDED[@]} -gt 0 ]; then
    OUTPUT+="### Added\n"
    for item in "${ADDED[@]}"; do OUTPUT+="${item}\n"; done
    OUTPUT+="\n"
fi

if [ ${#FIXED[@]} -gt 0 ]; then
    OUTPUT+="### Fixed\n"
    for item in "${FIXED[@]}"; do OUTPUT+="${item}\n"; done
    OUTPUT+="\n"
fi

if [ ${#CHANGED[@]} -gt 0 ]; then
    OUTPUT+="### Changed\n"
    for item in "${CHANGED[@]}"; do OUTPUT+="${item}\n"; done
    OUTPUT+="\n"
fi

if [ ${#REMOVED[@]} -gt 0 ]; then
    OUTPUT+="### Removed\n"
    for item in "${REMOVED[@]}"; do OUTPUT+="${item}\n"; done
    OUTPUT+="\n"
fi

echo -e "$OUTPUT"
