#!/usr/bin/env bash
set -euo pipefail

GIT_REPO="${1:-.}"
cd "$GIT_REPO"

LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)

echo "# Changelog"
echo ""
echo "All notable changes to this project will be documented in this file."
echo ""

if [ -n "$LAST_TAG" ]; then
    COMMITS=$(git log "$LAST_TAG"..HEAD --pretty=format:"%s||%h||%an||%ad" --date=short 2>/dev/null || true)
else
    COMMITS=$(git log --pretty=format:"%s||%h||%an||%ad" --date=short 2>/dev/null || true)
fi

if [ -z "$COMMITS" ]; then
    echo "No changes since last release."
    exit 0
fi

categorize() {
    local msg="$1"
    local upper=$(echo "$msg" | tr '[:lower:]' '[:upper:]')
    case "$msg" in
        feat:*|feature:*|add:*|implement*|introduce*|create*)
            echo "Added" ;;
        fix:*|bugfix:*|hotfix:*|patch:*|correct*|resolve*)
            echo "Fixed" ;;
        change:*|update:*|refactor:*|migrate:*|improve*|optimize*|redesign*)
            echo "Changed" ;;
        remove:*|delete:*|deprecate:*|drop:*|revert*)
            echo "Removed" ;;
        doc:*|document*|readme*|comment*)
            echo "Documentation" ;;
        test:*|spec:*|coverage*)
            echo "Testing" ;;
        chore:*|ci:*|bump:*|config*|build:*)
            echo "Maintenance" ;;
        security:*|vuln*|cve*|audit*)
            echo "Security" ;;
        perf:*|performanc*)
            echo "Performance" ;;
        style:*|format*|lint*)
            echo "Style" ;;
        *)
            echo "Changed" ;;
    esac
}

declare -A SECTIONS
SECTIONS["Added"]=""
SECTIONS["Fixed"]=""
SECTIONS["Changed"]=""
SECTIONS["Removed"]=""
SECTIONS["Documentation"]=""
SECTIONS["Testing"]=""
SECTIONS["Maintenance"]=""
SECTIONS["Security"]=""
SECTIONS["Performance"]=""
SECTIONS["Style"]=""

while IFS= read -r line; do
    [ -z "$line" ] && continue
    IFS='||' read -r msg hash author date <<< "$line"
    CAT=$(categorize "$msg")
    SECTIONS["$CAT"]="${SECTIONS[$CAT]}- $msg (#$hash, @$author, $date)
"
done <<< "$COMMITS"

for section in "Added" "Fixed" "Changed" "Removed" "Security" "Performance" "Documentation" "Testing" "Maintenance" "Style"; do
    entries="${SECTIONS[$section]}"
    if [ -n "$entries" ]; then
        echo "### $section"
        echo ""
        echo -e "$entries"
    fi
done
