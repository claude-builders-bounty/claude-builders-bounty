#!/usr/bin/env bash
# changelog.sh — Generate CHANGELOG.md from git history
# Usage: bash changelog.sh [--write] [--version X.Y.Z]

WRITE=false
VERSION=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --write) WRITE=true; shift ;;
        --version) VERSION="$2"; shift 2 ;;
        *) echo "Usage: $0 [--write] [--version X.Y.Z]" >&2; exit 1 ;;
    esac
done

if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not in a git repository" >&2; exit 1
fi

[ -z "$VERSION" ] && VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "Unreleased")
REPO_URL=$(git remote get-url origin 2>/dev/null | sed 's|git@github.com:|https://github.com/|; s|\.git$||' || echo "")
DATE=$(date +%Y-%m-%d)

OUTPUT="# Changelog"
OUTPUT="$OUTPUT"$'\n\n'"## [${VERSION}] - ${DATE}"

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
[ -n "$LAST_TAG" ] && LOG_RANGE="${LAST_TAG}..HEAD" || LOG_RANGE="HEAD"

ADDED=""; FIXED=""; CHANGED=""; REMOVED=""
DEPRECATED=""; SECURITY=""; PERF=""; DOCS=""; INFRA=""

while IFS='|' read -r HASH SUBJECT; do
    [ -z "$HASH" ] && continue
    SHORT_HASH=$(echo "$HASH" | cut -c1-8)
    [ -n "$REPO_URL" ] && LINK="[$SHORT_HASH](${REPO_URL}/commit/${SHORT_HASH})" || LINK="$SHORT_HASH"
    CLEAN=$(echo "$SUBJECT" | sed -E 's/^[a-z]+(\([^)]*\))?!?\s*:\s*//')
    ENTRY="  - ${CLEAN} (${LINK})"
    
    case "$SUBJECT" in
        feat:*|feature:*|add:*|implement:*|create:*|introduce:*)
            ADDED="${ADDED}"$'\n'"${ENTRY}" ;;
        fix:*|bugfix:*|bug:*|hotfix:*|resolve:*)
            FIXED="${FIXED}"$'\n'"${ENTRY}" ;;
        refactor:*|update:*|improve:*|change:*|modify:*)
            CHANGED="${CHANGED}"$'\n'"${ENTRY}" ;;
        remove:*|delete:*|drop:*|eliminate:*)
            REMOVED="${REMOVED}"$'\n'"${ENTRY}" ;;
        deprecat:*)
            DEPRECATED="${DEPRECATED}"$'\n'"${ENTRY}" ;;
        security:*|vuln:*|audit:*)
            SECURITY="${SECURITY}"$'\n'"${ENTRY}" ;;
        perf:*|performance:*|optimize:*)
            PERF="${PERF}"$'\n'"${ENTRY}" ;;
        docs:*|doc:*|readme:*)
            DOCS="${DOCS}"$'\n'"${ENTRY}" ;;
        ci:*|cd:*|build:*|chore\(*|dep:*|deploy:*)
            INFRA="${INFRA}"$'\n'"${ENTRY}" ;;
        *)
            LOW=$(echo "$SUBJECT" | tr '[:upper:]' '[:lower:]')
            case "$LOW" in
                *add*|*new*|*implement*|*create*)    ADDED="${ADDED}"$'\n'"${ENTRY}" ;;
                *fix*|*bug*|*patch*)                  FIXED="${FIXED}"$'\n'"${ENTRY}" ;;
                *remove*|*delete*|*drop*)              REMOVED="${REMOVED}"$'\n'"${ENTRY}" ;;
                *deprecat*)                           DEPRECATED="${DEPRECATED}"$'\n'"${ENTRY}" ;;
                *secur*|*vuln*|*cve*)                  SECURITY="${SECURITY}"$'\n'"${ENTRY}" ;;
                *perf*|*speed*|*optimize*)             PERF="${PERF}"$'\n'"${ENTRY}" ;;
                *doc*|*readme*)                        DOCS="${DOCS}"$'\n'"${ENTRY}" ;;
                *ci*|*build*|*deploy*|*docker*)        INFRA="${INFRA}"$'\n'"${ENTRY}" ;;
                *)                                     CHANGED="${CHANGED}"$'\n'"${ENTRY}" ;;
            esac ;;
    esac
done < <(git log --no-merges --format="%H|%s" "${LOG_RANGE}" 2>/dev/null || echo "")

add_section() {
    local h="$1" c="$2"
    [ -n "$c" ] && OUTPUT="$OUTPUT"$'\n\n'"### ${h}"$'\n'"$c"
}

add_section "Added" "$ADDED"
add_section "Fixed" "$FIXED"
add_section "Changed" "$CHANGED"
add_section "Deprecated" "$DEPRECATED"
add_section "Removed" "$REMOVED"
add_section "Security" "$SECURITY"
add_section "Performance" "$PERF"
add_section "Documentation" "$DOCS"
add_section "Infrastructure" "$INFRA"

[ -z "${ADDED}${FIXED}${CHANGED}${REMOVED}${DEPRECATED}${SECURITY}${PERF}${DOCS}${INFRA}" ] && OUTPUT="$OUTPUT"$'\n\n_No significant changes._'

if [ "$WRITE" = true ]; then
    printf "%s\n" "$OUTPUT" > CHANGELOG.md
    echo "Written to CHANGELOG.md"
else
    printf "%s\n" "$OUTPUT"
fi