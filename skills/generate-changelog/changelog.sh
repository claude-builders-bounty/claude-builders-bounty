#!/usr/bin/env bash
set -euo pipefail

OUT="${1:-CHANGELOG.md}"

# Fail before touching the output when Git history is unavailable.
git rev-parse --git-dir >/dev/null
git rev-parse --verify HEAD >/dev/null

LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"

if [ -n "$LAST_TAG" ]; then
    RANGE="${LAST_TAG}..HEAD"
else
    RANGE="HEAD"
fi

# Command substitution propagates git log errors under set -e.
# Process substitution would hide them and report a false success.
COMMITS_TEXT="$(git log "$RANGE" --no-merges --pretty=format:'%s')"
declare -a COMMITS=()
if [ -n "$COMMITS_TEXT" ]; then
    mapfile -t COMMITS <<< "$COMMITS_TEXT"
fi

declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()

for msg in "${COMMITS[@]}"; do

    case "$msg" in
        feat:*|feat!:*|feat\(*|add:*|add!:*|add\(*|new:*)
            ADDED+=("$msg")
            ;;

        fix:*|fix!:*|fix\(*|bug:*|hotfix:*)
            FIXED+=("$msg")
            ;;

        remove:*|remove!:*|remove\(*|removed:*|delete:*|delete!:*|delete\(*|drop:*|drop!:*|drop\(*)
            REMOVED+=("$msg")
            ;;

        *)
            CHANGED+=("$msg")
            ;;
    esac
done

{
    echo "# Changelog"
    echo
    echo "## Unreleased - $(date +%Y-%m-%d)"

    echo
    echo "### Added"
    if [ ${#ADDED[@]} -eq 0 ]; then
        echo "- None"
    else
        printf -- '- %s\n' "${ADDED[@]}"
    fi

    echo
    echo "### Fixed"
    if [ ${#FIXED[@]} -eq 0 ]; then
        echo "- None"
    else
        printf -- '- %s\n' "${FIXED[@]}"
    fi

    echo
    echo "### Changed"
    if [ ${#CHANGED[@]} -eq 0 ]; then
        echo "- None"
    else
        printf -- '- %s\n' "${CHANGED[@]}"
    fi

    echo
    echo "### Removed"
    if [ ${#REMOVED[@]} -eq 0 ]; then
        echo "- None"
    else
        printf -- '- %s\n' "${REMOVED[@]}"
    fi

} > "$OUT"

echo "Generated $OUT"
