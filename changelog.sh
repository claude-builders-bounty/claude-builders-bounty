#!/usr/bin/env bash
set -euo pipefail

OUTPUT="${1:-CHANGELOG.md}"

declare -A SECTIONS=(
    [Added]=""
    [Changed]=""
    [Fixed]=""
    [Removed]=""
)

if TAG=$(git describe --tags --abbrev=0 2>/dev/null); then
    RANGE="${TAG}..HEAD"
else
    RANGE="HEAD"
fi

while IFS=$'\t' read -r HASH SUBJECT; do
    [[ -z "$HASH" ]] && continue

    case "$SUBJECT" in
        feat:*|feature:*|add:*|added:*) SECTION="Added" ;;
        fix:*|bugfix:*|bug:*|fixed:*) SECTION="Fixed" ;;
        remove:*|removed:*|delete:*|deleted:*|revert:*) SECTION="Removed" ;;
        *) SECTION="Changed" ;;
    esac

    MESSAGE="$(printf '%s' "$SUBJECT" | sed -E \
        's/^(feat|feature|fix|bugfix|bug|add|added|change|changed|remove|removed|delete|deleted|revert)(\([^)]*\))?!?:[[:space:]]*//I')"

    SECTIONS["$SECTION"]+="- ${MESSAGE} (${HASH})"$'\n'
done < <(git log "$RANGE" --pretty=format:'%h%x09%s%n')

{
    printf '# Changelog\n\n'
    for SECTION in Added Changed Fixed Removed; do
        CONTENT="${SECTIONS[$SECTION]}"
        if [[ -n "$CONTENT" ]]; then
            printf '## %s\n\n' "$SECTION"
            printf '%s\n' "$CONTENT"
        fi
    done
} > "$OUTPUT"

printf 'Generated %s from %s\n' "$OUTPUT" "$RANGE"
