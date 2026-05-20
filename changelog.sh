#!/usr/bin/env bash
# changelog.sh — Generate structured CHANGELOG.md from git history
set -euo pipefail

TAG=""
ALL=false
OUTPUT="CHANGELOG.md"
REPO="."
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        -t|--tag)   TAG="$2"; shift 2 ;;
        -a|--all)   ALL=true; shift ;;
        -o|--output) OUTPUT="$2"; shift 2 ;;
        -r|--repo)  REPO="$2"; shift 2 ;;
        --dry-run)  DRY_RUN=true; shift ;;
        -h|--help)  echo "Usage: changelog.sh [-t TAG] [-a] [-o FILE] [-r PATH] [--dry-run]"; exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

cd "$REPO" 2>/dev/null || { echo "Error: cannot cd to $REPO"; exit 1; }
git rev-parse --is-inside-work-tree &>/dev/null || { echo "Error: not a git repository"; exit 1; }

REMOTE_URL=$(git config --get remote.origin.url 2>/dev/null || echo "")
REPO_URL=""
if echo "$REMOTE_URL" | grep -qE 'github\.com[:/]'; then
    REPO_URL="https://github.com/$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')"
fi

if [[ -z "$TAG" ]]; then
    TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
fi

categorize() {
    local msg="$1"
    local lower
    lower=$(echo "$msg" | tr '[:upper:]' '[:lower:]')

    # Conventional commits
    if echo "$lower" | grep -qE '^feat(\(.+\))?:\s'; then echo "Added"; return; fi
    if echo "$lower" | grep -qE '^fix(\(.+\))?:\s';  then echo "Fixed"; return; fi
    if echo "$lower" | grep -qE '^(refactor|style|perf|test|build|ci|docs)(\(.+\))?:\s'; then echo "Changed"; return; fi
    if echo "$lower" | grep -qE '^(chore|revert)(\(.+\))?:\s'; then
        if echo "$lower" | grep -qE 'remove|delete|drop'; then
            echo "Removed"
        else
            echo "Changed"
        fi
        return
    fi

    # Keyword fallback
    if echo "$lower" | grep -qE '^(add|create|implement|introduce|support)\s|added\b'; then echo "Added"; return; fi
    if echo "$lower" | grep -qE '^(fix|resolve|repair|patch|correct)\s|fixed\b|bugfix'; then echo "Fixed"; return; fi
    if echo "$lower" | grep -qE '^(update|refactor|improve|enhance|modify|bump|upgrade)\s|changed\b'; then echo "Changed"; return; fi
    if echo "$lower" | grep -qE '^(remove|delete|drop|deprecate|eliminate)\s'; then echo "Removed"; return; fi

    echo "Changed"
}

format_commit() {
    local hash="$1"
    local msg="$2"
    local display="$msg"

    # Strip conventional commit prefix
    display=$(echo "$display" | sed -E 's/^(feat|fix|refactor|chore|docs|style|perf|test|build|ci|revert)(\([^)]*\))?:\s*//')
    display="${display# }"

    # Capitalize first letter, remove trailing period
    display="$(echo "${display:0:1}" | tr '[:lower:]' '[:upper:]')${display:1}"
    display="${display%.}"

    if [[ -n "$REPO_URL" ]]; then
        echo "- ${display} ([${hash:0:7}](${REPO_URL}/commit/${hash}))"
    else
        echo "- ${display} (${hash:0:7})"
    fi
}

generate_section() {
    local since_tag="$1"
    local to_ref="${2:-HEAD}"
    local version_name="${since_tag:-Unreleased}"

    local date_str=""
    if [[ -n "$since_tag" ]]; then
        date_str=$(git log -1 --format="%ai" "$since_tag" 2>/dev/null | cut -d' ' -f1 || date +%Y-%m-%d)
    fi
    [[ -z "$date_str" ]] && date_str=$(date +%Y-%m-%d)

    local range="${since_tag:+${since_tag}..}${to_ref}"
    [[ -z "$since_tag" ]] && range="$to_ref"

    local count
    count=$(git log --no-merges --format="%H" "$range" 2>/dev/null | wc -l)
    if [[ "$count" -eq 0 ]]; then
        return
    fi

    echo "## ${version_name} (${date_str})"
    echo ""

    declare -A CATS
    CATS[Added]=""
    CATS[Fixed]=""
    CATS[Changed]=""
    CATS[Removed]=""

    while IFS=$'\t' read -r hash msg; do
        local cat
        cat=$(categorize "$msg")
        CATS[$cat]+="$(format_commit "$hash" "$msg")"$'\n'
    done < <(git log --no-merges --format="%H%x09%s" "$range" 2>/dev/null)

    for cat in "Added" "Fixed" "Changed" "Removed"; do
        if [[ -n "${CATS[$cat]}" ]]; then
            echo "### $cat"
            echo ""
            printf "%s" "${CATS[$cat]}"
            echo ""
        fi
    done
    echo ""
}

HEADER="# Changelog"
HEADER+=$'\n\n'
HEADER+="All notable changes to this project will be documented in this file."
HEADER+=$'\n'

BODY=""

if [[ "$ALL" == true ]]; then
    while IFS= read -r t; do
        BODY+=$(generate_section "$t" "$t")
    done < <(git tag --sort=-version:refname 2>/dev/null)
else
    if [[ -n "$TAG" ]]; then
        BODY+=$(generate_section "$TAG" "HEAD")
    else
        BODY+=$(generate_section "" "HEAD")
    fi
fi

FULL="${HEADER}"$'\n'"${BODY}"

if [[ "$DRY_RUN" == true ]]; then
    printf "%s" "$FULL"
else
    printf "%s" "$FULL" > "$OUTPUT"
    echo "✅ Changelog generated: ${OUTPUT}"
fi
