#!/usr/bin/env bash
# changelog.sh - Generate a structured CHANGELOG.md from git history.
#
# Usage:
#   bash changelog.sh [--repo DIR] [--since TAG] [--output FILE] [--help]
#
# Defaults:
#   --repo    .                 (current directory)
#   --since                    (auto: last git tag, or all commits if no tags)
#   --output  CHANGELOG.md      (written in --repo)

set -euo pipefail

REPO="."
SINCE=""
OUTPUT=""
HELP=0

# ---- helpers (defined early so they're available everywhere) ----------------

categorize() {
    local subject="$1"
    local body="$2"

    local prefix
    prefix=$(echo "$subject" | sed -E 's/^([a-zA-Z]+)(\([^)]+\))?!?:.*/\1/')

    if [[ "$body" == *"BREAKING CHANGE"* ]]; then
        echo "changed"
        return
    fi

    case "$prefix" in
        feat)               echo "added"   ;;
        fix)                echo "fixed"   ;;
        refactor|perf|style) echo "changed" ;;
        revert|removed)     echo "removed" ;;
        docs|test|chore|build|ci) echo "ignored" ;;
        *)                  echo "changed" ;;
    esac
}

emit_section() {
    local range="$1"
    local title="$2"

    echo ""
    echo "## [$title]"
    echo ""

    local -a added=() fixed=() changed=() removed=()

    local log_args=(--no-merges --format="%H %s%n%b---END---")
    if [[ -n "$range" ]]; then
        log_args+=("$range")
    fi

    # Use NUL-delimited iteration to handle multi-line bodies safely
    while IFS= read -r -d '' commit_block; do
        local subject body cat line
        subject=$(echo "$commit_block" | head -1 | sed 's/^[0-9a-f]\{40\} //')
        body=$(echo "$commit_block" | sed '1d;/^---END---$/d')

        cat=$(categorize "$subject" "$body")
        [[ "$cat" == "ignored" ]] && continue

        line="- ${subject}"

        case "$cat" in
            added)   added+=("$line")   ;;
            fixed)   fixed+=("$line")   ;;
            changed) changed+=("$line") ;;
            removed) removed+=("$line") ;;
        esac
    done < <(git log "${log_args[@]}" -z 2>/dev/null)

    local printed=0
    if [[ ${#added[@]} -gt 0 ]]; then
        echo "### Added"; for l in "${added[@]}"; do echo "$l"; done; echo ""; printed=1
    fi
    if [[ ${#fixed[@]} -gt 0 ]]; then
        echo "### Fixed"; for l in "${fixed[@]}"; do echo "$l"; done; echo ""; printed=1
    fi
    if [[ ${#changed[@]} -gt 0 ]]; then
        echo "### Changed"; for l in "${changed[@]}"; do echo "$l"; done; echo ""; printed=1
    fi
    if [[ ${#removed[@]} -gt 0 ]]; then
        echo "### Removed"; for l in "${removed[@]}"; do echo "$l"; done; echo ""; printed=1
    fi

    if [[ $printed -eq 0 ]]; then
        echo "_No notable changes._"
        echo ""
    fi
}

# ---- arg parsing ------------------------------------------------------------

while [[ $# -gt 0 ]]; do
    case "$1" in
        --repo)    REPO="$2";   shift 2 ;;
        --since)   SINCE="$2";  shift 2 ;;
        --output)  OUTPUT="$2"; shift 2 ;;
        --help|-h) HELP=1;      shift   ;;
        *) echo "ERROR: unknown arg: $1" >&2; exit 2 ;;
    esac
done

if [[ "$HELP" -eq 1 ]]; then
    sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'
    exit 0
fi

cd "$REPO" || { echo "ERROR: cannot cd to $REPO" >&2; exit 1; }
[[ -d .git ]] || { echo "ERROR: $REPO is not a git repo" >&2; exit 1; }

OUTPUT="${OUTPUT:-CHANGELOG.md}"

LATEST_TAG=$(git tag --sort=-v:refname 2>/dev/null | head -1 || true)

if [[ -z "$SINCE" ]]; then
    SINCE="$LATEST_TAG"
fi

# Header
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),"
    echo "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)."
    echo ""
} > "$OUTPUT"

TAGS=$(git tag --sort=-v:refname 2>/dev/null || true)
if [[ -n "$TAGS" ]]; then
    PREV=""
    TAG_ARR=($TAGS)
    N=${#TAG_ARR[@]}

    # Walk tags newest → oldest
    for ((i=0; i<N; i++)); do
        tag="${TAG_ARR[$i]}"
        if [[ $i -eq 0 ]]; then
            section_title="Unreleased"
            range="$tag..HEAD"
        else
            section_title="$tag"
            prev="${TAG_ARR[$((i-1))]}"
            range="$tag..$prev"
        fi
        emit_section "$range" "$section_title" >> "$OUTPUT"
    done

    # initial range: oldest tag → all commits before it
    last="${TAG_ARR[$((N-1))]}"
    emit_section "$last" "${TAG_ARR[$((N-1))]} — initial and prior" >> "$OUTPUT"
else
    emit_section "" "Unreleased" >> "$OUTPUT"
fi

echo "Wrote $OUTPUT"