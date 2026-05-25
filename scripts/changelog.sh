#!/usr/bin/env bash
# changelog.sh — Generate structured CHANGELOG.md from git history
# Usage: bash scripts/changelog.sh [--write] [--since v1.0.0] [--tag v1.1.0]

set -euo pipefail

SINCE=""
NEW_TAG=""
OUTPUT_FILE=""

usage() {
    cat <<'HELP'
Generate a structured CHANGELOG.md from git history.

Usage:
    bash changelog.sh                    Print to stdout
    bash changelog.sh --write            Overwrite CHANGELOG.md
    bash changelog.sh --since v1.0.0     From tag v1.0.0
    bash changelog.sh --tag v1.1.0       Set version header
    bash changelog.sh --output FILE      Write to FILE
HELP
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h) usage ;;
        --since) SINCE="$2"; shift ;; 
        --tag) NEW_TAG="$2"; shift ;;
        --write) OUTPUT_FILE="${OUTPUT_FILE:-CHANGELOG.md}" ;;
        --output) OUTPUT_FILE="$2"; shift ;;
        *) SINCE="${SINCE:-$1}" ;;
    esac
    shift
done

# Default version
if [[ -z "$NEW_TAG" ]]; then
    NEW_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.1.0")
fi

# Default since - last tag or first commit
if [[ -z "$SINCE" ]]; then
    PREV=$(git tag --sort=-version:refname 2>/dev/null | head -2 | tail -1 || echo "")
    if [[ -n "$PREV" ]]; then
        SINCE="$PREV"
    else
        SINCE=$(git log --reverse --format="%H" 2>/dev/null | head -1 || echo "HEAD")
    fi
fi

DATE=$(date +"%Y-%m-%d")
REMOTE=$(git remote get-url origin 2>/dev/null | sed 's/\.git$//' | sed 's|git@github.com:|https://github.com/|')

# Read commits
COMMITS=$(git log "${SINCE}..HEAD" --format="%H|%s" --no-merges 2>/dev/null || true)
if [[ -z "$COMMITS" ]]; then
    echo "No new commits since $SINCE"
    exit 0
fi

# Categories
ADDED=""; FIXED=""; CHANGED=""; REMOVED=""; SECURITY=""; TOTAL=0

while IFS='|' read -r hash msg; do
    [[ -z "$hash" ]] && continue
    lmsg="${msg,,}"
    cat="Changed"
    if [[ "$lmsg" =~ ^(feat|feature|add|implement|create|new) ]]; then cat="Added"
    elif [[ "$lmsg" =~ ^(fix|bugfix|bug|correct|resolve|patch|hotfix) ]]; then cat="Fixed"
    elif [[ "$lmsg" =~ ^(remove|delete|drop|deprecat|cleanup) ]]; then cat="Removed"
    elif [[ "$lmsg" =~ ^(security|vuln|cve|auth|xss|csrf) ]]; then cat="Security"
    elif [[ "$lmsg" =~ ^(refactor|update|change|migrate|improve|bump|upgrade|chore) ]]; then cat="Changed"
    elif [[ "$lmsg" =~ (add|new|feat|support|implement) ]]; then cat="Added"
    elif [[ "$lmsg" =~ (fix|bug|correct|error|crash) ]]; then cat="Fixed"
    elif [[ "$lmsg" =~ (remove|delete|drop|deprecat) ]]; then cat="Removed"
    elif [[ "$lmsg" =~ (security|vuln|cve|xss) ]]; then cat="Security"
    fi
    clean=$(echo "$msg" | sed -E 's/^(feat|feature|fix|bugfix|refactor|chore|docs|style|test|perf|ci|build|revert)(\([^)]*\))?: //')
    entry="- ${clean:-$msg} ([${hash:0:7}]($REMOTE/commit/$hash))\n"
    case "$cat" in
        Added) ADDED+="$entry" ;; Fixed) FIXED+="$entry" ;; Changed) CHANGED+="$entry" ;;
        Removed) REMOVED+="$entry" ;; Security) SECURITY+="$entry" ;;
    esac
    TOTAL=$((TOTAL + 1))
done <<< "$COMMITS"

# Build output
output="# Changelog\n\n## [$NEW_TAG] - $DATE\n\n"
[[ -n "$ADDED" ]]    && output+="### Added\n\n$ADDED\n"
[[ -n "$FIXED" ]]    && output+="### Fixed\n\n$FIXED\n"
[[ -n "$CHANGED" ]]  && output+="### Changed\n\n$CHANGED\n"
[[ -n "$REMOVED" ]]  && output+="### Removed\n\n$REMOVED\n"
[[ -n "$SECURITY" ]] && output+="### Security\n\n$SECURITY\n"
output+="---\n*$TOTAL changes in this release*\n"

if [[ -n "$OUTPUT_FILE" ]]; then
    echo -e "$output" > "$OUTPUT_FILE"
    echo "Wrote $OUTPUT_FILE ($TOTAL changes)"
else
    echo -e "$output"
fi
