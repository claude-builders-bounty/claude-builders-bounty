#!/usr/bin/env bash
#
# changelog.sh — generate a structured CHANGELOG.md from a project's git history.
#
# Zero dependencies beyond git + coreutils. Works on macOS, Linux and Git Bash
# on Windows.
#
# Usage:
#   bash changelog.sh                          # since the last tag, append to CHANGELOG.md
#   bash changelog.sh --dry-run                # print the block, write nothing
#   bash changelog.sh --version v2.1.0         # force the version heading
#   bash changelog.sh --from v1.9.0 --to HEAD  # explicit range
#   bash changelog.sh --stdout                 # only print (CI / release notes)
#   bash changelog.sh --log-file log.txt       # replay a captured log (tests, no git needed)
#
# Categorisation is Conventional-Commits first, keyword fallback second:
#   feat                    -> Added
#   fix                     -> Fixed
#   perf|refactor|style     -> Changed
#   docs|test|build|ci|chore|deps -> Changed
#   revert|remove|deprecate -> Removed
#   anything else gets keyword-scanned (add/fix/remove/...) and defaults to Changed.
#
set -euo pipefail

PROG="$(basename "$0")"
FROM=""
TO="HEAD"
VERSION=""
OUTPUT="CHANGELOG.md"
PRINT_ONLY=0
DRY_RUN=0
LOG_FILE=""
REPO_URL_OVERRIDE=""
INCLUDE_MERGES=0

usage() {
    sed -n '2,40p' "$0" | sed 's/^# \{0,1\}//'
}

die() { printf '%s: error: %s\n' "$PROG" "$1" >&2; exit 1; }
note() { printf '%s: %s\n' "$PROG" "$1" >&2; }

while [ $# -gt 0 ]; do
    case "$1" in
        --from)       FROM="${2:?--from needs a ref}"; shift 2 ;;
        --from=*)     FROM="${1#*=}"; shift ;;
        --to)         TO="${2:?--to needs a ref}"; shift 2 ;;
        --to=*)       TO="${1#*=}"; shift ;;
        --version)    VERSION="${2:?--version needs a value}"; shift 2 ;;
        --version=*)  VERSION="${1#*=}"; shift ;;
        --output)     OUTPUT="${2:?--output needs a path}"; shift 2 ;;
        --output=*)   OUTPUT="${1#*=}"; shift ;;
        --log-file)   LOG_FILE="${2:?--log-file needs a path}"; shift 2 ;;
        --log-file=*) LOG_FILE="${1#*=}"; shift ;;
        --repo-url)   REPO_URL_OVERRIDE="${2:?--repo-url needs a value}"; shift 2 ;;
        --repo-url=*) REPO_URL_OVERRIDE="${1#*=}"; shift ;;
        --stdout)     PRINT_ONLY=1; shift ;;
        --dry-run)    DRY_RUN=1; shift ;;
        --merges)     INCLUDE_MERGES=1; shift ;;
        -h|--help)    usage; exit 0 ;;
        *)            die "unknown argument '$1' (try --help)" ;;
    esac
done

# ---------------------------------------------------------------- repo context
REPO_URL=""
if [ -n "$REPO_URL_OVERRIDE" ]; then
    REPO_URL="$REPO_URL_OVERRIDE"
elif command -v git >/dev/null 2>&1; then
    REPO_URL="$(git remote get-url origin 2>/dev/null || true)"
fi
# git@github.com:owner/repo.git -> https://github.com/owner/repo
case "$REPO_URL" in
    git@*:*) REPO_URL="https://$(printf '%s' "${REPO_URL#git@}" | sed 's|:|/|')" ;;
    ssh://git@*) REPO_URL="https://${REPO_URL#ssh://git@}" ;;
esac
REPO_URL="${REPO_URL%.git}"
REPO_URL="${REPO_URL%/}"

# ------------------------------------------------------------------ log source
WORK="$(mktemp -d "${TMPDIR:-/tmp}/changelog.XXXXXX")" 2>/dev/null || WORK="./.changelog-tmp.$$"
[ -d "$WORK" ] || { mkdir -p "$WORK"; }
trap 'rm -rf "$WORK"' EXIT

RAW="$WORK/raw.log"

if [ -n "$LOG_FILE" ]; then
    [ -f "$LOG_FILE" ] || die "log file not found: $LOG_FILE"
    cat "$LOG_FILE" > "$RAW"
    RANGE_DESC="replayed log ${LOG_FILE}"
else
    command -v git >/dev/null 2>&1 || die "git not found and no --log-file given"
    git rev-parse --git-dir >/dev/null 2>&1 || die "not inside a git repository"

    TO_SHA="$(git rev-parse --verify "${TO}^{commit}" 2>/dev/null)" || die "cannot resolve --to '$TO'"

    if [ -z "$FROM" ]; then
        # last tag reachable from TO; fall back to the root commit (= whole history)
        FROM="$(git describe --tags --abbrev=0 "$TO_SHA" 2>/dev/null || true)"
        if [ -z "$FROM" ]; then
            FROM="$(git rev-list --max-parents=0 "$TO_SHA" | tail -n 1)"
            note "no tag found — using the full history from root commit ${FROM:0:7}"
        fi
    fi

    RANGE_DESC="${FROM}..${TO}"
    MERGE_FLAG=""
    [ "$INCLUDE_MERGES" -eq 1 ] || MERGE_FLAG="--no-merges"
    # shellcheck disable=SC2086
    git -c core.quotepath=false log --date=short --pretty=format:'%H%x1f%ad%x1f%s' \
        $MERGE_FLAG "${FROM}..${TO}" > "$RAW"
fi

if [ ! -s "$RAW" ]; then
    note "no commits in range ${RANGE_DESC:-<none>} — nothing to do"
    [ "$PRINT_ONLY" -eq 1 ] || [ "$DRY_RUN" -eq 1 ] || exit 0
    printf '## %s - %s\n\n_No changes._\n' "${VERSION:-Unreleased}" "$(date +%Y-%m-%d)"
    exit 0
fi

# ------------------------------------------------------------- categorisation
: > "$WORK/added"; : > "$WORK/fixed"; : > "$WORK/changed"; : > "$WORK/removed"

# note: `|| [ -n "$SHA" ]` keeps the last line when the log has no trailing newline
while IFS=$'\x1f' read -r SHA DATE SUBJECT || [ -n "${SHA:-}" ]; do
    [ -n "${SHA:-}" ] || continue
    SHORT="${SHA:0:7}"

    # drop release/version-bump noise, keep everything else
    case "$SUBJECT" in
        [0-9]*.[0-9]*.[0-9]*)               continue ;;
        Merge\ pull\ request*)              continue ;;
        Merge\ branch*)                     continue ;;
        chore\(release\)*)                  continue ;;
        chore:\ release*)                   continue ;;
    esac

    CAT="Changes"
    BODY="$SUBJECT"
    SCOPE=""
    BREAKING=""
    TYPE=""

    # Conventional Commits: type(scope)!: subject
    if [[ "$SUBJECT" =~ ^([A-Za-z]+)(\(([^\)]+)\))?(!)?:\ *(.*)$ ]]; then
        TYPE="$(printf '%s' "${BASH_REMATCH[1]}" | tr '[:upper:]' '[:lower:]')"
        SCOPE="${BASH_REMATCH[3]:-}"
        BREAKING="${BASH_REMATCH[4]:-}"
        BODY="${BASH_REMATCH[5]}"
    fi

    case "$TYPE" in
        feat|feature|add)                     CAT="Added" ;;
        fix|bugfix|hotfix|patch)              CAT="Fixed" ;;
        perf|refactor|style|docs|doc|test|tests|build|ci|chore|deps|revert-style) CAT="Changed" ;;
        remove|removal|revert|deprecate)      CAT="Removed" ;;
        *)
            LOWER="$(printf '%s' "$SUBJECT" | tr '[:upper:]' '[:lower:]')"
            case "$LOWER" in
                *"fix "*|*"fix:"*|*bug*|*hotfix*|*"patch "*)       CAT="Fixed" ;;
                *"remove "*|*"removed "*|*"delete "*|*"drop "*|*"deprecat"*) CAT="Removed" ;;
                *"add "*|*"added "*|*"implement "*|*"introduce "*|*"support for "*) CAT="Added" ;;
                *)                                                CAT="Changed" ;;
            esac
            TYPE=""
            ;;
    esac

    # trailing "(#123)" style refs -> pull request links
    PRS=""
    if [[ "$BODY" =~ \(\#([0-9]+)\)\ *$ ]] || [[ "$BODY" =~ \ \(\#([0-9]+)\) ]]; then
        PR_NUM="${BASH_REMATCH[1]}"
        if [ -n "$REPO_URL" ]; then
            PRS="[#$PR_NUM]($REPO_URL/pull/$PR_NUM)"
        else
            PRS="#$PR_NUM"
        fi
        BODY="$(printf '%s' "$BODY" | sed -E 's/\s?\(#[0-9]+\)[[:space:]]*$//')"
    fi

    # commit link
    if [ -n "$REPO_URL" ]; then
        SHA_REF="[\`$SHORT\`]($REPO_URL/commit/$SHA)"
    else
        SHA_REF="\`$SHORT\`"
    fi

    REFS="$SHA_REF"
    [ -z "$PRS" ] || REFS="$PRS, $SHA_REF"

    LABEL=""
    [ -n "$SCOPE" ] && LABEL="**${SCOPE}:** "
    [ -n "$BREAKING" ] && LABEL="**BREAKING** ${LABEL}"

    printf -- '- %s%s (%s)\n' "$LABEL" "$BODY" "$REFS" >> "$WORK/$(printf '%s' "$CAT" | tr '[:upper:]' '[:lower:]')"
done < "$RAW"

# ------------------------------------------------------------------ assembling
BLOCK="$WORK/block.md"
{
    printf '## [%s] - %s\n' "${VERSION:-Unreleased}" "$(date +%Y-%m-%d)"
    for pair in "Added:added" "Fixed:fixed" "Changed:changed" "Removed:removed"; do
        TITLE="${pair%%:*}"; FILE="${pair##*:}"
        if [ -s "$WORK/$FILE" ]; then
            printf '\n### %s\n\n' "$TITLE"
            sort -f "$WORK/$FILE"
        fi
    done
    printf '\n'
} > "$BLOCK"

if [ "$PRINT_ONLY" -eq 1 ] || [ "$DRY_RUN" -eq 1 ]; then
    cat "$BLOCK"
    exit 0
fi

# ------------------------------------------------------------------- prepending
if [ -f "$OUTPUT" ]; then
    cp "$OUTPUT" "$WORK/old.md"
    # keep everything above the first "## " heading, insert the new block there
    awk -v blockfile="$BLOCK" '
        BEGIN { inserted = 0 }
        !inserted && /^## / {
            while ((getline line < blockfile) > 0) print line
            inserted = 1
        }
        { print }
        END {
            if (!inserted) {
                while ((getline line < blockfile) > 0) print line
            }
        }
    ' "$WORK/old.md" > "$WORK/new.md"
    mv "$WORK/new.md" "$OUTPUT"
else
    {
        printf '# Changelog\n\nAll notable changes to this project are documented here.\n'
        printf 'Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). '
        printf 'Generated by `generate-changelog`.\n\n'
        cat "$BLOCK"
    } > "$OUTPUT"
fi

note "wrote ${OUTPUT} (${RANGE_DESC:-replayed log})"
