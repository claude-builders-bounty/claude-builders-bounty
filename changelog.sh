#!/usr/bin/env bash

set -euo pipefail

OUTPUT_FILE="CHANGELOG.md"

latest_tag=$(git describe --tags --abbrev=0 2>/dev/null || true)

if [[ -n "$latest_tag" ]]; then
    commits=$(git log "${latest_tag}..HEAD" --pretty=format:'%s')
    title="Changes since ${latest_tag}"
else
    commits=$(git log --pretty=format:'%s')
    title="Changes"
fi

added=""
fixed=""
changed=""
removed=""

while IFS= read -r commit; do
    [[ -z "$commit" ]] && continue

    lower=$(printf '%s' "$commit" | tr '[:upper:]' '[:lower:]')

    case "$lower" in
        feat:*|feature:*|add:*|added:*)
            added="${added}- ${commit}"$'\n'
            ;;
        fix:*|fixed:*|bugfix:*)
            fixed="${fixed}- ${commit}"$'\n'
            ;;
        remove:*|removed:*|delete:*|deleted:*)
            removed="${removed}- ${commit}"$'\n'
            ;;
        *)
            changed="${changed}- ${commit}"$'\n'
            ;;
    esac
done <<< "$commits"

{
    printf '# Changelog\n\n'
    printf '## %s\n\n' "$title"

    if [[ -n "$added" ]]; then
        printf '### Added\n\n%s\n' "$added"
    fi

    if [[ -n "$fixed" ]]; then
        printf '### Fixed\n\n%s\n' "$fixed"
    fi

    if [[ -n "$changed" ]]; then
        printf '### Changed\n\n%s\n' "$changed"
    fi

    if [[ -n "$removed" ]]; then
        printf '### Removed\n\n%s\n' "$removed"
    fi
} > "$OUTPUT_FILE"

printf 'Generated %s\n' "$OUTPUT_FILE"
