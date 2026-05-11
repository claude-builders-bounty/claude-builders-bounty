#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history.
#
# Usage:
#   bash changelog.sh                  # prepend a new release section to CHANGELOG.md
#   bash changelog.sh --stdout         # print to stdout instead of writing
#   bash changelog.sh --from <ref>     # override the "since" ref (default: last tag)
#   bash changelog.sh --to <ref>       # override the "until" ref (default: HEAD)
#   bash changelog.sh --version <tag>  # label the section (default: Unreleased)
#   bash changelog.sh --output <file>  # output file (default: CHANGELOG.md)
#
# Categorization (Keep a Changelog):
#   Added    — feat, add, new
#   Fixed    — fix, bugfix, hotfix, patch
#   Changed  — refactor, perf, change, update, chore, docs, style, build, ci, test, deps
#   Removed  — remove, delete, revert, drop
#   Other    — anything that does not match (kept under "Changed" so nothing is dropped)

set -euo pipefail

OUT="CHANGELOG.md"
FROM=""
TO="HEAD"
VERSION=""
TO_STDOUT=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --stdout)  TO_STDOUT=1; shift ;;
        --from)    FROM="$2"; shift 2 ;;
        --to)      TO="$2"; shift 2 ;;
        --version) VERSION="$2"; shift 2 ;;
        --output)  OUT="$2"; shift 2 ;;
        -h|--help)
            sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//'
            exit 0 ;;
        *) echo "unknown arg: $1" >&2; exit 2 ;;
    esac
done

if ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo "error: not inside a git repository" >&2
    exit 1
fi

# Resolve the "since" ref: explicit --from > last tag > entire history.
if [[ -z "$FROM" ]]; then
    if FROM=$(git describe --tags --abbrev=0 2>/dev/null); then
        RANGE="${FROM}..${TO}"
        RANGE_LABEL="since \`${FROM}\`"
    else
        RANGE="$TO"
        RANGE_LABEL="full history (no tags found)"
    fi
else
    RANGE="${FROM}..${TO}"
    RANGE_LABEL="since \`${FROM}\`"
fi

# Default version label: the user-supplied tag, or the resolved --to if it is a tag,
# or "Unreleased" otherwise.
if [[ -z "$VERSION" ]]; then
    if git rev-parse "refs/tags/${TO}" >/dev/null 2>&1; then
        VERSION="$TO"
    else
        VERSION="Unreleased"
    fi
fi

DATE=$(date -u +%Y-%m-%d)

# Collect commits as "SUBJECT|SHORTSHA" lines. Merge commits are excluded; they
# rarely carry user-facing intent and would pollute the changelog.
mapfile -t COMMITS < <(git log "$RANGE" --no-merges --pretty=format:'%s|%h' --reverse 2>/dev/null || true)

if [[ ${#COMMITS[@]} -eq 0 ]]; then
    echo "no commits found in range: $RANGE" >&2
    exit 0
fi

ADDED=()
FIXED=()
CHANGED=()
REMOVED=()

# Conventional-commit-style prefix matcher. We strip an optional scope like
# "feat(ui):" and an optional "!" breaking-change marker before matching.
classify() {
    local subject="$1"
    local lower
    lower=$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')

    # Strip leading "type(scope)!:" or "type!:" or "type:" — capture the type.
    local type=""
    if [[ "$lower" =~ ^([a-z]+)(\([^\)]+\))?!?:[[:space:]] ]]; then
        type="${BASH_REMATCH[1]}"
    fi

    case "$type" in
        feat|add|added|new)             echo added ;;
        fix|bugfix|hotfix|patch)        echo fixed ;;
        remove|removed|delete|deleted|revert|drop)
                                        echo removed ;;
        refactor|perf|change|changed|update|updated|chore|docs|doc|style|build|ci|test|tests|deps|dep)
                                        echo changed ;;
        *)
            # Fallback: keyword sniff on the subject line.
            case "$lower" in
                *" add "*|"add "*|*" added "*|"adds "*|*" introduce "*|"introduce "*|*" implement "*|"implement "*)
                    echo added ;;
                *" fix "*|"fix "*|*" fixes "*|*" fixed "*|*" resolve "*|"resolve "*|*" patch "*)
                    echo fixed ;;
                *" remove "*|"remove "*|*" removed "*|*" delete "*|"delete "*|*" drop "*|*"revert"*)
                    echo removed ;;
                *)
                    echo changed ;;
            esac
            ;;
    esac
}

# Strip the conventional-commit prefix from a subject for display, and
# capitalize the first character so the bullet reads cleanly.
prettify() {
    local subject="$1"
    local stripped
    stripped=$(printf '%s' "$subject" | sed -E 's/^[a-zA-Z]+(\([^)]+\))?!?:[[:space:]]*//')
    # Capitalize first letter (POSIX-safe).
    printf '%s%s' "$(printf '%s' "${stripped:0:1}" | tr '[:lower:]' '[:upper:]')" "${stripped:1}"
}

for line in "${COMMITS[@]}"; do
    subject="${line%|*}"
    sha="${line##*|}"
    bucket=$(classify "$subject")
    entry="- $(prettify "$subject") (\`${sha}\`)"
    case "$bucket" in
        added)   ADDED+=("$entry") ;;
        fixed)   FIXED+=("$entry") ;;
        removed) REMOVED+=("$entry") ;;
        *)       CHANGED+=("$entry") ;;
    esac
done

render_section() {
    local title="$1"; shift
    local -a items=("$@")
    if [[ ${#items[@]} -eq 0 ]]; then return; fi
    printf '\n### %s\n' "$title"
    printf '%s\n' "${items[@]}"
}

NEW_SECTION=$(
    printf '## [%s] - %s\n' "$VERSION" "$DATE"
    printf '\n_Changes %s._\n' "$RANGE_LABEL"
    render_section "Added"   "${ADDED[@]+"${ADDED[@]}"}"
    render_section "Changed" "${CHANGED[@]+"${CHANGED[@]}"}"
    render_section "Fixed"   "${FIXED[@]+"${FIXED[@]}"}"
    render_section "Removed" "${REMOVED[@]+"${REMOVED[@]}"}"
    printf '\n'
)

HEADER="# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
"

if [[ $TO_STDOUT -eq 1 ]]; then
    printf '%s\n%s' "$HEADER" "$NEW_SECTION"
    exit 0
fi

if [[ -f "$OUT" ]]; then
    # Prepend the new section just below the header. We detect the header by the
    # first "## " heading; if none exists, append after the existing content.
    TMP=$(mktemp)
    if grep -nE '^## ' "$OUT" >/dev/null 2>&1; then
        FIRST=$(grep -nE '^## ' "$OUT" | head -1 | cut -d: -f1)
        head -n $((FIRST - 1)) "$OUT" > "$TMP"
        printf '%s\n\n' "$NEW_SECTION" >> "$TMP"
        tail -n +"$FIRST" "$OUT" >> "$TMP"
    else
        cat "$OUT" > "$TMP"
        printf '\n%s\n' "$NEW_SECTION" >> "$TMP"
    fi
    mv "$TMP" "$OUT"
else
    printf '%s\n%s' "$HEADER" "$NEW_SECTION" > "$OUT"
fi

echo "wrote $OUT (${#ADDED[@]} added, ${#CHANGED[@]} changed, ${#FIXED[@]} fixed, ${#REMOVED[@]} removed)"
